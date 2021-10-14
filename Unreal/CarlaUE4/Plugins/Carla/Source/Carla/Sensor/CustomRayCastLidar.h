// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once


#include "Carla/Actor/ActorDefinition.h"
#include "Carla/Sensor/LidarDescription.h"
#include "Carla/Sensor/Sensor.h"
#include "Carla/Sensor/CustomRayCastSemanticLidar.h"
#include "Carla/Actor/ActorBlueprintFunctionLibrary.h"

#include <compiler/disable-ue4-macros.h>
#include <carla/sensor/data/CustomLidarData.h>
#include <compiler/enable-ue4-macros.h>

#include "CustomRayCastLidar.generated.h"

/// A ray-cast based Lidar sensor.
UCLASS()
class CARLA_API ACustomRayCastLidar : public ACustomRayCastSemanticLidar
{
  GENERATED_BODY()

  using FCustomLidarData = carla::sensor::data::CustomLidarData;
  using FCustomDetection = carla::sensor::data::CustomLidarDetection;

public:
  static FActorDefinition GetSensorDefinition();

  ACustomRayCastLidar(const FObjectInitializer &ObjectInitializer);
  virtual void Set(const FActorDescription &Description) override;
  virtual void Set(const FLidarDescription &LidarDescription) override;

  virtual void PostPhysTick(UWorld *World, ELevelTick TickType, float DeltaTime);

private:
  /// Compute the received intensity of the point
  float ComputeIntensity(const FCustomSemanticDetection& RawDetection) const;
  FCustomDetection ComputeDetection(const FHitResult& HitInfo, const FTransform& SensorTransf) const;

  void PreprocessRays(uint32_t Channels, uint32_t MaxPointsPerChannel) override;
  bool PostprocessDetection(FCustomDetection& Detection) const;

  void ComputeAndSaveDetections(const FTransform& SensorTransform) override;

  FCustomLidarData CustomLidarData;

  /// Enable/Disable general dropoff of lidar points
  bool DropOffGenActive;

  /// Slope for the intensity dropoff of lidar points, it is calculated
  /// throught the dropoff limit and the dropoff at zero intensity
  /// The points is kept with a probality alpha*Intensity + beta where
  /// alpha = (1 - dropoff_zero_intensity) / droppoff_limit
  /// beta = (1 - dropoff_zero_intensity)
  float DropOffAlpha;
  float DropOffBeta;
};
