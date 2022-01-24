// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include "Carla.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Carla/Sensor/IntensityCamera.h"

#include "Runtime/RenderCore/Public/RenderingThread.h"

AIntensityCamera::AIntensityCamera() 
{
	Camera = FindComponentByClass<class USceneCaptureComponent2D>();
	//RenderTarget = Camera->TextureTarget;
	ConstructorHelpers::FObjectFinder<UTextureRenderTarget2D> RenderTargetAsset(TEXT("/Game/RekosTestingBox/Intensity/RT_IntensityValues"));
	RenderTarget = RenderTargetAsset.Object;
}

void AIntensityCamera::GetIntensity(float& IntensityValue)
{
	MyTexture2D = RenderTarget->ConstructTexture2D(this, FString("Tex2D"), EObjectFlags::RF_NoFlags);
	//FTexturePlatformData* Data = MyTexture2D->PlatformData;
	//const void* Table = Data->Mips[0].BulkData.LockReadOnly();
	//Data->Mips[0].BulkData.Unlock();

	//const uint16* Tab2 = StaticCast<const uint16*>(Table);
	//int k = 4 * (128 * 256 + 128);
	//float R = Tab2[k];
	//IntensityValue = R;

	const FColor* FormatedImageData = reinterpret_cast<const FColor*>(MyTexture2D->PlatformData->Mips[0].BulkData.Lock(LOCK_READ_ONLY));
	MyTexture2D->PlatformData->Mips[0].BulkData.Unlock();
	FColor PixelColor = FormatedImageData[128 * 256 + 128];
	IntensityValue = PixelColor.B/255.0f;

	//const FColor* FormatedImageData = static_cast<const FColor*>(MyTexture2D->PlatformData->Mips[0].BulkData.LockReadOnly());

	//FColor PixelColor = FormatedImageData[128*256+128];
	//IntensityValue = PixelColor.A;

	//MyTexture2D->PlatformData->Mips[0].BulkData.Unlock();
}