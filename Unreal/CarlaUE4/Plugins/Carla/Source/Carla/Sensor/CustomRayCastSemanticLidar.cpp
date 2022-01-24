// Copyright (c) 2020 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include <PxScene.h>
#include <cmath>
#include "Carla.h"
#include "Carla/Actor/ActorBlueprintFunctionLibrary.h"
#include "Carla/Sensor/CustomRayCastSemanticLidar.h"

#include <compiler/disable-ue4-macros.h>
#include "carla/geom/Math.h"
#include <compiler/enable-ue4-macros.h>

#include "DrawDebugHelpers.h"
#include "Engine/CollisionProfile.h"
#include "Runtime/Engine/Classes/Kismet/KismetMathLibrary.h"
#include "Runtime/Core/Public/Async/ParallelFor.h"
#include <list>
#include <iostream>
#include <fstream>
using namespace std;

namespace crp = carla::rpc;

FActorDefinition ACustomRayCastSemanticLidar::GetSensorDefinition()
{
  return UActorBlueprintFunctionLibrary::MakeLidarDefinition(TEXT("custom_ray_cast_semantic"));
}

ACustomRayCastSemanticLidar::ACustomRayCastSemanticLidar(const FObjectInitializer& ObjectInitializer)
  : Super(ObjectInitializer)
{
  PrimaryActorTick.bCanEverTick = true;
  static ConstructorHelpers::FClassFinder<ASceneCapture2D> ClassFinder(TEXT("/Game/RekosTestingBox/Intensity/BP_Int.BP_Int_C"));
  if (ClassFinder.Class)
      SubClass = ClassFinder.Class;
}

void ACustomRayCastSemanticLidar::Set(const FActorDescription &ActorDescription)
{
  Super::Set(ActorDescription);
  FLidarDescription LidarDescription;
  UActorBlueprintFunctionLibrary::SetLidar(ActorDescription, LidarDescription);
  Set(LidarDescription);
}

void ACustomRayCastSemanticLidar::Set(const FLidarDescription &LidarDescription)
{
  Description = LidarDescription;
  CustomSemanticLidarData = FCustomSemanticLidarData(Description.Channels);
  CreateLasers();
  PointsPerChannel.resize(Description.Channels);
}

void ACustomRayCastSemanticLidar::CreateLasers()
{
  GetIntCamera();
  const auto NumberOfLasers = Description.Channels;
  check(NumberOfLasers > 0u);
  const float DeltaAngle = NumberOfLasers == 1u ? 0.f :
    (Description.UpperFovLimit - Description.LowerFovLimit) /
    static_cast<float>(NumberOfLasers - 1);
  LaserAngles.Empty(NumberOfLasers);
  for(auto i = 0u; i < NumberOfLasers; ++i)
  {
    const float VerticalAngle =
        Description.UpperFovLimit - static_cast<float>(i) * DeltaAngle;
    LaserAngles.Emplace(VerticalAngle);
  }
}

void ACustomRayCastSemanticLidar::GetIntCamera()
{
    FActorSpawnParameters SpawnParams;
    FTransform ActorTransf = GetTransform();
    FVector Loc = ActorTransf.GetLocation();
    FRotator Rot = ActorTransf.Rotator();

    IntensityCamera = GetWorld()->SpawnActor<AIntensityCamera>(SubClass, Loc, Rot, SpawnParams);
    IntensityCamera->AttachToActor(this, FAttachmentTransformRules::SnapToTargetNotIncludingScale);
}

void ACustomRayCastSemanticLidar::PostPhysTick(UWorld *World, ELevelTick TickType, float DeltaTime)
{
  TRACE_CPUPROFILER_EVENT_SCOPE(ACustomRayCastSemanticLidar::PostPhysTick);
  SimulateLidar(DeltaTime);

  {
    TRACE_CPUPROFILER_EVENT_SCOPE_STR("Send Stream");
    auto DataStream = GetDataStream(*this);
    DataStream.Send(*this, CustomSemanticLidarData, DataStream.PopBufferFromPool());
  }
}

void ACustomRayCastSemanticLidar::SimulateLidar(const float DeltaTime)
{
  TRACE_CPUPROFILER_EVENT_SCOPE(ACustomRayCastSemanticLidar::SimulateLidar);
  const uint32 ChannelCount = Description.Channels;
  const uint32 PointsToScanWithOneLaser =
    FMath::RoundHalfFromZero(
        Description.PointsPerSecond * DeltaTime / float(ChannelCount));

  if (PointsToScanWithOneLaser <= 0)
  {
    UE_LOG(
        LogCarla,
        Warning,
        TEXT("%s: no points requested this frame, try increasing the number of points per second."),
        *GetName());
    return;
  }

  check(ChannelCount == LaserAngles.Num());

  const float CurrentHorizontalAngle = carla::geom::Math::ToDegrees(
      CustomSemanticLidarData.GetHorizontalAngle());
  const float AngleDistanceOfTick = Description.RotationFrequency * Description.HorizontalFov
      * DeltaTime;
  const float AngleDistanceOfLaserMeasure = AngleDistanceOfTick / PointsToScanWithOneLaser;

  ResetRecordedHits(ChannelCount, PointsToScanWithOneLaser);
  PreprocessRays(ChannelCount, PointsToScanWithOneLaser);

  auto *World = GetWorld();
  UCarlaGameInstance *GameInstance = UCarlaStatics::GetGameInstance(World);
  auto *Episode = GameInstance->GetCarlaEpisode();
  auto *Weather = Episode->GetWeather();
  FWeatherParameters w = Weather->GetCurrentWeather(); //current weather
  srand((unsigned)time( NULL )); //seed the random

  GetWorld()->GetPhysicsScene()->GetPxScene()->lockRead();
  {
    TRACE_CPUPROFILER_EVENT_SCOPE(ParallelFor);
    ParallelFor(ChannelCount, [&](int32 idxChannel) {
      TRACE_CPUPROFILER_EVENT_SCOPE(ParallelForTask);

      FCollisionQueryParams TraceParams = FCollisionQueryParams(FName(TEXT("Laser_Trace")), true, this);
      TraceParams.bTraceComplex = true;
      TraceParams.bReturnPhysicalMaterial = false;
      
      for (auto idxPtsOneLaser = 0u; idxPtsOneLaser < PointsToScanWithOneLaser; idxPtsOneLaser++) {
        FHitResult HitResult;
        const float VertAngle = LaserAngles[idxChannel];
        const float HorizAngle = std::fmod(CurrentHorizontalAngle + AngleDistanceOfLaserMeasure
            * idxPtsOneLaser, Description.HorizontalFov) - Description.HorizontalFov / 2;
        const bool PreprocessResult = RayPreprocessCondition[idxChannel][idxPtsOneLaser];

        if (PreprocessResult && ShootLaser(VertAngle, HorizAngle, HitResult, TraceParams, w)) {
          WritePointAsync(idxChannel, HitResult);
        }
      };
    });
  }
  GetWorld()->GetPhysicsScene()->GetPxScene()->unlockRead();

  FTransform ActorTransf = GetTransform();
  ComputeAndSaveDetections(ActorTransf);

  const float HorizontalAngle = carla::geom::Math::ToRadians(std::fmod(CurrentHorizontalAngle + AngleDistanceOfTick, Description.HorizontalFov));
  CustomSemanticLidarData.SetHorizontalAngle(HorizontalAngle);
}

void ACustomRayCastSemanticLidar::ResetRecordedHits(uint32_t Channels, uint32_t MaxPointsPerChannel) {
  RecordedHits.resize(Channels);

  for (auto& hits : RecordedHits) {
    hits.clear();
    hits.reserve(MaxPointsPerChannel);
  }
}

void ACustomRayCastSemanticLidar::PreprocessRays(uint32_t Channels, uint32_t MaxPointsPerChannel) {
  RayPreprocessCondition.resize(Channels);

  for (auto& conds : RayPreprocessCondition) {
    conds.clear();
    conds.resize(MaxPointsPerChannel);
    std::fill(conds.begin(), conds.end(), true);
  }
}

void ACustomRayCastSemanticLidar::WritePointAsync(uint32_t channel, FHitResult &detection) {
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);
  DEBUG_ASSERT(GetChannelCount() > channel);
  RecordedHits[channel].emplace_back(detection);
}

void ACustomRayCastSemanticLidar::ComputeAndSaveDetections(const FTransform& SensorTransform) {
	TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);
  for (auto idxChannel = 0u; idxChannel < Description.Channels; ++idxChannel)
    PointsPerChannel[idxChannel] = RecordedHits[idxChannel].size();
  CustomSemanticLidarData.ResetMemory(PointsPerChannel);

  for (auto idxChannel = 0u; idxChannel < Description.Channels; ++idxChannel) {
    for (auto& hit : RecordedHits[idxChannel]) {
      FCustomSemanticDetection detection;
      ComputeRawDetection(hit, SensorTransform, detection);
      CustomSemanticLidarData.WritePointSync(detection);
    }
  }

  CustomSemanticLidarData.WriteChannelCount(PointsPerChannel);
}

void ACustomRayCastSemanticLidar::ComputeRawDetection(const FHitResult& HitInfo, const FTransform& SensorTransf, FCustomSemanticDetection& Detection) const
{
    const FVector HitPoint = HitInfo.ImpactPoint;
    Detection.point = SensorTransf.Inverse().TransformPosition(HitPoint);

    const FVector VecInc = - (HitPoint - SensorTransf.GetLocation()).GetSafeNormal();
    Detection.cos_inc_angle = FVector::DotProduct(VecInc, HitInfo.ImpactNormal);

    const FActorRegistry &Registry = GetEpisode().GetActorRegistry();

    const AActor* actor = HitInfo.Actor.Get();
    Detection.object_idx = 0;

    
    if (HitInfo.Component == nullptr) 
    {
      Detection.object_tag = static_cast<uint32_t>(23);
    } else {
      Detection.object_tag = static_cast<uint32_t>(HitInfo.Component->CustomDepthStencilValue);
    }

    
    //Detection.object_tag = static_cast<uint32_t>(HitInfo.Component->CustomDepthStencilValue);

    if (actor != nullptr) {

      const FCarlaActor* view = Registry.FindCarlaActor(actor);
      if(view)
        Detection.object_idx = view->GetActorId();

    }
    else {
      //UE_LOG(LogCarla, Warning, TEXT("Actor not valid %p!!!!"), actor);
    }
}

bool ACustomRayCastSemanticLidar::CalculateNewHitPoint(FHitResult& HitInfo, float rain_amount, FVector end_trace, FVector LidarBodyLoc) const
{
  FVector max_distance = end_trace; //lidar max range
  FVector start_point = LidarBodyLoc; //start point is lidar position
	if (HitInfo.bBlockingHit) //If linetrace hits something
	{
		max_distance = HitInfo.ImpactPoint; //max_distance = where we got hit with linetrace
	}

  FVector vector = end_trace - start_point; 
	FVector new_start_point = start_point + 0.01 * vector; //make start point away from center of lidar
	FVector new_vector = max_distance - new_start_point; //new vector from new start point to end point
  float random = (float) rand()/double(RAND_MAX); //random floating number between 0-1
  FVector new_hitpoint = new_start_point + random * new_vector; //Generate new point from new start point to end point
	float distance = FVector::Dist(start_point, new_hitpoint)/100; //distance beteen new_hitpoint and start point (divide by 100 to get meters)
	
  float vis = 60 / (2000 - (rain_amount*18.4f));
  float prob = vis*exp(-pow((distance-20.0f),2.0f)/pow(8.0f,2.0f))+vis*exp(-pow((distance-38.0f),2.0f)/pow(18.0f,2.0f)); //value between 0-1 this is the probability of trace to hit snowflake at certain distances

  float r = (float)rand() / double(RAND_MAX); //random between 0-1
	if (r < prob) //if random is smaller than probability from formula we hit the trace to snowflake
	{
		HitInfo.ImpactPoint = new_hitpoint; //assign new hitpoint
        HitInfo.Component = nullptr; //set component to null if hitpoint is snowflake
		return true;
	}
	else {
		return false;
	}
}

bool ACustomRayCastSemanticLidar::CustomDropOff(const float rain_amount) const //custom drop off rate for lidar hits according to rainamount(snow)
{
  float random = (float) rand()/ double(RAND_MAX);
  float dropoff = rain_amount * 0.003;
  if (random < dropoff) //dropoff max value is 0.3 at rain_amount value 100
  {
    return false;
  } else {
    return true;
  }
  
}

bool ACustomRayCastSemanticLidar::ShootLaser(const float VerticalAngle, const float HorizontalAngle, FHitResult& HitResult, FCollisionQueryParams& TraceParams, FWeatherParameters w) const
{
  TRACE_CPUPROFILER_EVENT_SCOPE_STR(__FUNCTION__);

  FHitResult HitInfo(ForceInit);

  FTransform ActorTransf = GetTransform();
  FVector LidarBodyLoc = ActorTransf.GetLocation();
  FRotator LidarBodyRot = ActorTransf.Rotator();

  FRotator LaserRot (VerticalAngle, HorizontalAngle, 0);  // float InPitch, float InYaw, float InRoll
  FRotator ResultRot = UKismetMathLibrary::ComposeRotators(
    LaserRot,
    LidarBodyRot
  );

  const auto Range = Description.Range;
  FVector EndTrace = Range * UKismetMathLibrary::GetForwardVector(ResultRot) + LidarBodyLoc;

  //ROTATE INTENSITY CAMERA
  IntensityCamera->SetActorRotation(ResultRot);
  /////////////////////////////////////////

  GetWorld()->ParallelLineTraceSingleByChannel(
    HitInfo,
    LidarBodyLoc,
    EndTrace,
    ECC_GameTraceChannel2,
    TraceParams,
    FCollisionResponseParams::DefaultResponseParam
  );

  //ADD intensity from camera to Time slot of HitResult
  float f = 0.0f;
  IntensityCamera->GetIntensity(f);
  HitInfo.Time = f;
  /////////////////////////////////////////////////////

  float temp = w.Temperature;
  float rain_amount = w.Precipitation;
  bool keepPoint = true;
  if (HitInfo.bBlockingHit) { 
	  if (temp < 0 && rain_amount > 0) //If it is snowing
	  {
		  CalculateNewHitPoint(HitInfo, rain_amount, EndTrace, LidarBodyLoc);
          keepPoint = CustomDropOff(rain_amount);
	  }
    HitResult = HitInfo; //equal to new hitpoint or the old one
    return keepPoint;
  } else { //If no hit is acquired
    if (temp < 0 && rain_amount > 0) //If it is snowing
	{
	    if(CalculateNewHitPoint(HitInfo, rain_amount, EndTrace, LidarBodyLoc)) //if new hitpoint is made
        {
            HitResult = HitInfo;
            return CustomDropOff(rain_amount);
        }
	}
    return false;
  }
}
