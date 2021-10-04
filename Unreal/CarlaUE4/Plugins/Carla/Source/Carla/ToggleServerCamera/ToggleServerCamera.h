// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// Copyright(c) 2021 FrostBit Software Lab
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include "GameFramework/Actor.h"
#include "ToggleServerCamera.generated.h"

UCLASS(Abstract)
class CARLA_API AToggleServerCamera : public AActor
{
	GENERATED_BODY()

public:

	AToggleServerCamera(const FObjectInitializer& ObjectInitializer);

	UFUNCTION(BlueprintImplementableEvent, BlueprintCallable, Category = Gameplay)
	void ToggleCamera();
};
