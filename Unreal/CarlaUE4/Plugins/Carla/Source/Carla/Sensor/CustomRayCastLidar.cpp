// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include <PxScene.h>
#include <cmath>
#include "Carla.h"
#include "Carla/Sensor/CustomRayCastLidar.h"
#include "Carla/Actor/ActorBlueprintFunctionLibrary.h"
#include "carla/geom/Math.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "MaterialExpressionIO.h"
#include <compiler/disable-ue4-macros.h>
#include "carla/geom/Math.h"
#include "carla/geom/Location.h"
#include <compiler/enable-ue4-macros.h>
#include "Components/StaticMeshComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/CollisionProfile.h"
#include "Runtime/Engine/Classes/Kismet/KismetMathLibrary.h"

FActorDefinition ACustomRayCastLidar::GetSensorDefinition()
{
  return UActorBlueprintFunctionLibrary::MakeLidarDefinition(TEXT("custom_ray_cast"));
}


ACustomRayCastLidar::ACustomRayCastLidar(const FObjectInitializer& ObjectInitializer)
  : Super(ObjectInitializer) {

  RandomEngine = CreateDefaultSubobject<URandomEngine>(TEXT("RandomEngine"));
  SetSeed(Description.RandomSeed);
}

void ACustomRayCastLidar::Set(const FActorDescription &ActorDescription)
{
  ASensor::Set(ActorDescription);
  FLidarDescription LidarDescription;
  UActorBlueprintFunctionLibrary::SetLidar(ActorDescription, LidarDescription);
  Set(LidarDescription);
}

void ACustomRayCastLidar::Set(const FLidarDescription &LidarDescription)
{
  Description = LidarDescription;
  CustomLidarData = FCustomLidarData(Description.Channels);
  CreateLasers();
  PointsPerChannel.resize(Description.Channels);

  // Compute drop off model parameters
  DropOffBeta = 1.0f - Description.DropOffAtZeroIntensity;
  DropOffAlpha = Description.DropOffAtZeroIntensity / Description.DropOffIntensityLimit;
  DropOffGenActive = Description.DropOffGenRate > std::numeric_limits<float>::epsilon();
}

void ACustomRayCastLidar::PostPhysTick(UWorld *World, ELevelTick TickType, float DeltaTime)
{
  TRACE_CPUPROFILER_EVENT_SCOPE(ACustomRayCastLidar::PostPhysTick);
  SimulateLidar(DeltaTime);

  {
    TRACE_CPUPROFILER_EVENT_SCOPE_STR("Send Stream");
    auto DataStream = GetDataStream(*this);
    DataStream.Send(*this, CustomLidarData, DataStream.PopBufferFromPool());
  }
}

float ACustomRayCastLidar::ComputeIntensity(const FCustomSemanticDetection& RawDetection) const
{
  const carla::geom::Location HitPoint = RawDetection.point;
  const float Distance = HitPoint.Length();

  const float AttenAtm = Description.AtmospAttenRate;
  const float AbsAtm = exp(-AttenAtm * Distance);

  const float IntRec = AbsAtm;

  return IntRec;
}

ACustomRayCastLidar::FCustomDetection ACustomRayCastLidar::ComputeDetection(const FHitResult& HitInfo, const FTransform& SensorTransf) const
{
  FHitResult Hit = HitInfo;
  FCustomDetection Detection;
  const FVector HitPoint = HitInfo.ImpactPoint;
  Detection.point = SensorTransf.Inverse().TransformPosition(HitPoint);
  auto *World = GetWorld();
  UCarlaGameInstance *GameInstance = UCarlaStatics::GetGameInstance(World);
  auto *Episode = GameInstance->GetCarlaEpisode();
  auto *Weather = Episode->GetWeather();
  FWeatherParameters w = Weather->GetCurrentWeather(); //current weather
  const float Distance = Detection.point.Length();
  float AttenAtm = 0.019+0.017*w.RelativeHumidity;
  float AbsAtm = exp(-AttenAtm * Distance);
  float IntRec = AbsAtm;

  if (HitInfo.Component == nullptr) { //snowflakes dont have component
      Detection.intensity = 0.1;
  }
  else {
  Detection.intensity = IntRec;
  }
  return Detection;
}

  void ACustomRayCastLidar::PreprocessRays(uint32_t Channels, uint32_t MaxPointsPerChannel) {
    Super::PreprocessRays(Channels, MaxPointsPerChannel);

    for (auto ch = 0u; ch < Channels; ch++) {
      for (auto p = 0u; p < MaxPointsPerChannel; p++) {
        RayPreprocessCondition[ch][p] = !(DropOffGenActive && RandomEngine->GetUniformFloat() < Description.DropOffGenRate);
      }
    }
  }

  bool ACustomRayCastLidar::PostprocessDetection(FCustomDetection& Detection) const
  {
    auto *World = GetWorld();
    UCarlaGameInstance *GameInstance = UCarlaStatics::GetGameInstance(World);
    auto *Episode = GameInstance->GetCarlaEpisode();
    auto *Weather = Episode->GetWeather();
    FWeatherParameters w = Weather->GetCurrentWeather(); //current weather

    if (-0.00024*w.Temperature+0.011 > std::numeric_limits<float>::epsilon()) {
      const auto ForwardVector = Detection.point.MakeUnitVector();
      const auto Noise = ForwardVector * RandomEngine->GetNormalDistribution(0.0f, -0.00024*w.Temperature+0.011);
      Detection.point += Noise;
    }

    const float Intensity = Detection.intensity;
    if(Intensity > Description.DropOffIntensityLimit)
      return true;
    else
      return RandomEngine->GetUniformFloat() < DropOffAlpha * Intensity + DropOffBeta;
  }

  void ACustomRayCastLidar::ComputeAndSaveDetections(const FTransform& SensorTransform) {
    for (auto idxChannel = 0u; idxChannel < Description.Channels; ++idxChannel)
      PointsPerChannel[idxChannel] = RecordedHits[idxChannel].size();

    CustomLidarData.ResetMemory(PointsPerChannel);

    for (auto idxChannel = 0u; idxChannel < Description.Channels; ++idxChannel) {
      for (auto& hit : RecordedHits[idxChannel]) {
        FCustomDetection Detection = ComputeDetection(hit, SensorTransform);
        if (PostprocessDetection(Detection))
            CustomLidarData.WritePointSync(Detection);
        else
          PointsPerChannel[idxChannel]--;
      }
    }

    CustomLidarData.WriteChannelCount(PointsPerChannel);
  }
