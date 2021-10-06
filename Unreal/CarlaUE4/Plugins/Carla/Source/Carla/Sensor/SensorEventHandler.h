// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// Copyright(c) 2021 FrostBit Software Lab
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include "GameFramework/Actor.h"
#include "SensorEventHandler.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FLevelEventDelegate_CameraAdded);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FLevelEventDelegate_CameraRemoved);

UCLASS(Abstract)
class CARLA_API ASensorEventHandler : public AActor
{
	GENERATED_BODY()

public:

	ASensorEventHandler(const FObjectInitializer& ObjectInitializer);

	UPROPERTY(BlueprintAssignable, BlueprintCallable)
	FLevelEventDelegate_CameraAdded CameraAdded;

	UPROPERTY(BlueprintAssignable, BlueprintCallable)
	FLevelEventDelegate_CameraRemoved CameraRemoved;

	/*UFUNCTION(BlueprintCallable)
	static Test();*/

};
