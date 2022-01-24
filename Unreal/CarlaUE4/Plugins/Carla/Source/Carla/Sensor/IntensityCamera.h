// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include "Carla/Actor/ActorDefinition.h"
#include "Carla/Sensor/PixelReader.h"
#include "Carla/Sensor/ShaderBasedSensor.h"
#include "Engine/SceneCapture2D.h"
#include "Components/ActorComponent.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Runtime/Engine/Classes/Engine/TextureRenderTarget2D.h"
#include "Engine/Texture2D.h"

#include "IntensityCamera.generated.h"

/// A sensor that captures images from the scene.
UCLASS()
class CARLA_API AIntensityCamera : public ASceneCapture2D
{
  GENERATED_BODY()

public:
	AIntensityCamera();

	UPROPERTY(EditAnywhere, Category = "Intensity")
	float Intensity;

	//Get current intensity value
	UFUNCTION(BlueprintCallable, Category="Intensity")
	void GetIntensity(float& IntensityValue);

protected:
	USceneCaptureComponent2D* Camera;
	UTextureRenderTarget2D* RenderTarget;
	UTexture2D* MyTexture2D;

};
