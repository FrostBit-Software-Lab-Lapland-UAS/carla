// Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// Copyright(c) 2021 FrostBit Software Lab
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include <PxScene.h>

#include "Carla.h"
#include "Carla/Sensor/Radar.h"
#include "Carla/Actor/ActorBlueprintFunctionLibrary.h"
#include "Kismet/KismetMathLibrary.h"
#include "Runtime/Core/Public/Async/ParallelFor.h"

#include "carla/geom/Math.h"

//#include "carla/Game/

//#include "carla/Game/CarlaGameInstance.h"


FActorDefinition ARadar::GetSensorDefinition()
{
  return UActorBlueprintFunctionLibrary::MakeRadarDefinition();
}

ARadar::ARadar(const FObjectInitializer& ObjectInitializer)
  : Super(ObjectInitializer)
{
  PrimaryActorTick.bCanEverTick = true;

  RandomEngine = CreateDefaultSubobject<URandomEngine>(TEXT("RandomEngine"));

  TraceParams = FCollisionQueryParams(FName(TEXT("Laser_Trace")), true, this);
  TraceParams.bTraceComplex = true;
  TraceParams.bReturnPhysicalMaterial = false;

}

void ARadar::Set(const FActorDescription &ActorDescription)
{
  Super::Set(ActorDescription);
  UActorBlueprintFunctionLibrary::SetRadar(ActorDescription, this);
}

void ARadar::SetHorizontalFOV(float NewHorizontalFOV)
{
  HorizontalFOV = NewHorizontalFOV;
}

void  ARadar::SetVerticalFOV(float NewVerticalFOV)
{
  VerticalFOV = NewVerticalFOV;
}

void ARadar::SetRange(float NewRange)
{
  Range = NewRange;
}

void ARadar::SetPointsPerSecond(int NewPointsPerSecond)
{
  PointsPerSecond = NewPointsPerSecond;
  RadarData.SetResolution(PointsPerSecond);
}

void ARadar::BeginPlay()
{
  Super::BeginPlay();

  PrevLocation = GetActorLocation();
}

void ARadar::PostPhysTick(UWorld *World, ELevelTick TickType, float DeltaTime)
{
  CalculateCurrentVelocity(DeltaTime);

  RadarData.Reset();
  SendLineTraces(DeltaTime);

  auto DataStream = GetDataStream(*this);
  DataStream.Send(*this, RadarData, DataStream.PopBufferFromPool());
}

void ARadar::CalculateCurrentVelocity(const float DeltaTime)
{
  const FVector RadarLocation = GetActorLocation();
  CurrentVelocity = (RadarLocation - PrevLocation) / DeltaTime;
  PrevLocation = RadarLocation;
}

void ARadar::SendLineTraces(float DeltaTime)
{

  constexpr float TO_METERS = 1e-2;
  const FTransform& ActorTransform = GetActorTransform();
  const FRotator& TransformRotator = ActorTransform.Rotator();
  const FVector& RadarLocation = GetActorLocation();
  const FVector& ForwardVector = GetActorForwardVector();
  const FVector TransformXAxis = ActorTransform.GetUnitAxis(EAxis::X);
  const FVector TransformYAxis = ActorTransform.GetUnitAxis(EAxis::Y);
  const FVector TransformZAxis = ActorTransform.GetUnitAxis(EAxis::Z);

  // Maximum radar radius in horizontal and vertical direction
  const float MaxRx = FMath::Tan(FMath::DegreesToRadians(HorizontalFOV * 0.5f)) * Range;
  const float MaxRy = FMath::Tan(FMath::DegreesToRadians(VerticalFOV * 0.5f)) * Range;
  const int NumPoints = (int)(PointsPerSecond * DeltaTime);


  // WinterSim experimental stuff
  // Some fun stuff to read about Radar performance in rain/snowy, foggy conditions
  // https://www.researchgate.net/publication/331723697_The_Impact_of_Adverse_Weather_Conditions_on_Autonomous_Vehicles_Examining_how_rain_snow_fog_and_hail_affect_the_performance_of_a_self-driving_car
  // https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6068852/
  // in the research, they found that Radar detection range dropped 
  // ~26% on 50mm/hr rain (12.5 Precipitation value) and ~55% on 400 mm/hr rain (100.0 Precipitation value)
  // this is *very* simplified radar distance drop off rate 
  // based on current Weather Precipitation and FogDensity values

  // Get weather parameters
  auto *World = GetWorld();
  UCarlaGameInstance *GameInstance = UCarlaStatics::GetGameInstance(World);
  auto *Episode = GameInstance->GetCarlaEpisode();
  auto *Weather = Episode->GetWeather();
  FWeatherParameters w = Weather->GetCurrentWeather();
  float precipitation = w.Precipitation;						// Precipitation range is from 0.0 to 100.0
  float fog = w.FogDensity;										// FogDensity range is from 0.0 to 100.0
 
  // calculate drop off rate
  // multiply precipitation value by magic number 2.08 to get drop off percetange
  // Example: for 12.0 precipitation value (50 mm/hr rain) drop off is ~26 %
  float dropOffRate = (precipitation * 2.08) / 100;												
  if (dropOffRate > 0.55) {
	  dropOffRate = 0.55;										// cap drop off rate to 55%
  }
  dropOffRate = (100 - (precipitation * dropOffRate)) / 100;	// drop off rate, range: 0.45 to 1.00

  // Calculate new Radar Range
  float dropRatePerFogValue = 25;								// some random drop off value I just invented
  float radarDistance = 10000 - (fog * dropRatePerFogValue);	// calculate new radar distance from base distance (100m)
  float newRange = radarDistance * dropOffRate;					// multiply radar distance with dropOffRate
  if (Range != newRange)
  {
   SetRange(newRange);
   //UE_LOG(LogTemp, Warning, TEXT("Text, %f, %f"), Range, precipitation);
  }

  // Generate the parameters of the rays in a deterministic way
  Rays.clear();
  Rays.resize(NumPoints);
  for (int i = 0; i < Rays.size(); i++) {
    Rays[i].Radius = RandomEngine->GetUniformFloat();
    Rays[i].Angle = RandomEngine->GetUniformFloatInRange(0.0f, carla::geom::Math::Pi2<float>());
    Rays[i].Hitted = false;
  }

  FCriticalSection Mutex;
  GetWorld()->GetPhysicsScene()->GetPxScene()->lockRead();
  ParallelFor(NumPoints, [&](int32 idx) {
    FHitResult OutHit(ForceInit);
    const float Radius = Rays[idx].Radius;
    const float Angle  = Rays[idx].Angle;

    float Sin, Cos;
    FMath::SinCos(&Sin, &Cos, Angle);

    const FVector EndLocation = RadarLocation + TransformRotator.RotateVector({
      Range,
      MaxRx * Radius * Cos,
      MaxRy * Radius * Sin
    });

    const bool Hitted = GetWorld()->LineTraceSingleByChannel(
      OutHit,
      RadarLocation,
      EndLocation,
      ECC_GameTraceChannel2,
      TraceParams,
      FCollisionResponseParams::DefaultResponseParam
    );

    const TWeakObjectPtr<AActor> HittedActor = OutHit.Actor;
    if (Hitted && HittedActor.Get()) {
      Rays[idx].Hitted = true;

      Rays[idx].RelativeVelocity = CalculateRelativeVelocity(OutHit, RadarLocation);

      Rays[idx].AzimuthAndElevation = FMath::GetAzimuthAndElevation (
        (EndLocation - RadarLocation).GetSafeNormal() * newRange,
        TransformXAxis,
        TransformYAxis,
        TransformZAxis
      );

      Rays[idx].Distance = OutHit.Distance * TO_METERS;
    }
  });
  GetWorld()->GetPhysicsScene()->GetPxScene()->unlockRead();

  // Write the detections in the output structure
  for (auto& ray : Rays) {
    if (ray.Hitted) {
      RadarData.WriteDetection({
        ray.RelativeVelocity,
        ray.AzimuthAndElevation.X,
        ray.AzimuthAndElevation.Y,
        ray.Distance
      });
    }
  }
}

float ARadar::CalculateRelativeVelocity(const FHitResult& OutHit, const FVector& RadarLocation)
{
  constexpr float TO_METERS = 1e-2;

  const TWeakObjectPtr<AActor> HittedActor = OutHit.Actor;
  const FVector TargetVelocity = HittedActor->GetVelocity();
  const FVector TargetLocation = OutHit.ImpactPoint;
  const FVector Direction = (TargetLocation - RadarLocation).GetSafeNormal();
  const FVector DeltaVelocity = (TargetVelocity - CurrentVelocity);
  const float V = TO_METERS * FVector::DotProduct(DeltaVelocity, Direction);

  return V;
}