// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.



#pragma once

#include "Carla/Sensor/Sensor.h"

#include "Carla/Actor/ActorDefinition.h"
#include "Carla/Sensor/LidarDescription.h"
#include "Carla/Actor/ActorBlueprintFunctionLibrary.h"

#include <compiler/disable-ue4-macros.h>
#include <carla/sensor/data/CustomSemanticLidarData.h>
#include <compiler/enable-ue4-macros.h>
#include <list>
#include <iostream>
#include <fstream>

#include "Engine/SceneCapture2D.h"
#include "Carla/Sensor/IntensityCamera.h"
//#include "C:/carla/Unreal/CarlaUE4/Source/CarlaUE4/Public/IntensityCamera.h"


#include "CustomRayCastSemanticLidar.generated.h"


/// A ray-cast based Lidar sensor.
UCLASS()
class CARLA_API ACustomRayCastSemanticLidar : public ASensor
{
  GENERATED_BODY()

protected:

  using FCustomSemanticLidarData = carla::sensor::data::CustomSemanticLidarData;
  using FCustomSemanticDetection = carla::sensor::data::CustomSemanticLidarDetection;

public:
  static FActorDefinition GetSensorDefinition();

  ACustomRayCastSemanticLidar(const FObjectInitializer &ObjectInitializer);

  virtual void Set(const FActorDescription &Description) override;
  virtual void Set(const FLidarDescription &LidarDescription);

  //Intensity Camera
  UPROPERTY(EditAnywhere);
  AIntensityCamera* IntensityCamera;
  TSubclassOf<class AIntensityCamera> SubClass;
  void GetIntCamera();

protected:
  virtual void PostPhysTick(UWorld *World, ELevelTick TickType, float DeltaTime) override;

  /// Creates a Laser for each channel.
  void CreateLasers();

  /// Updates LidarMeasurement with the points read in DeltaTime.
  void SimulateLidar(const float DeltaTime);

  /// Shoot a laser ray-trace, return whether the laser hit something.
  bool ShootLaser(const float VerticalAngle, float HorizontalAngle, FHitResult &HitResult, FCollisionQueryParams& TraceParams, FWeatherParameters w) const;

  /// Calculate new hitpoint for linetrace if it is snowing
  bool CalculateNewHitPoint(FHitResult& HitInfo, float rain_amount, FVector end_trace, FVector LidarBodyLoc) const;

  bool CustomDropOff(float rain_amount) const;

  /// Method that allow to preprocess if the rays will be traced.
  virtual void PreprocessRays(uint32_t Channels, uint32_t MaxPointsPerChannel);

  /// Compute all raw detection information
  void ComputeRawDetection(const FHitResult &HitInfo, const FTransform &SensorTransf, FCustomSemanticDetection &Detection) const;

  /// Saving the hits the raycast returns per channel
  void WritePointAsync(uint32_t Channel, FHitResult &Detection);

  /// Clear the recorded data structure
  void ResetRecordedHits(uint32_t Channels, uint32_t MaxPointsPerChannel);

  /// This method uses all the saved FHitResults, compute the
  /// RawDetections and then send it to the LidarData structure.
  virtual void ComputeAndSaveDetections(const FTransform &SensorTransform);

  UPROPERTY(EditAnywhere)
  FLidarDescription Description;

  TArray<float> LaserAngles;

  std::vector<std::vector<FHitResult>> RecordedHits;
  std::vector<std::vector<bool>> RayPreprocessCondition;
  std::vector<uint32_t> PointsPerChannel;

private:
  FCustomSemanticLidarData CustomSemanticLidarData;

};
