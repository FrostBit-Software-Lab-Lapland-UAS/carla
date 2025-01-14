// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// Copyright(c) 2021 FrostBit Software Lab
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include "WeatherParameters.generated.h"

USTRUCT(BlueprintType)
struct CARLA_API FWeatherParameters
{
  GENERATED_BODY()

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float Cloudiness = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float Precipitation = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float PrecipitationDeposits = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float WindIntensity = 0.35f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "360.0", UIMin = "0.0", UIMax = "360.0"))
  float SunAzimuthAngle = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "-90.0", ClampMax = "90.0", UIMin = "-90.0", UIMax = "90.0"))
  float SunAltitudeAngle = 75.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float FogDensity = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", UIMin = "0.0", UIMax = "1000.0"))
  float FogDistance = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", UIMin = "0.0", UIMax = "10.0"))
  float FogFalloff = 0.2f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float Wetness = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float ScatteringIntensity = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "5.0", UIMin = "0.0", UIMax = "5.0"))
  float MieScatteringScale = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "2.0", UIMin = "0.0", UIMax = "2.0"))
  float RayleighScatteringScale = 0.0331f;
  
  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float SnowAmount = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float SnowDirtyness = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "-40.0", ClampMax = "40.0", UIMin = "-40.0", UIMax = "40.0"))
  float Temperature = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float IceAmount = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin = "1.0", ClampMax = "3.0", UIMin = "1.0", UIMax = "3.0"))
  float ParticleSize = 1.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float RelativeHumidity = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float Dewpoint = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "0.0", ClampMax = "360.0", UIMin = "0.0", UIMax = "360.0"))
  float WindDirection = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "-100.0", ClampMax = "100.0", UIMin = "-100.0", UIMax = "100.0"))
  float Latitude = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "-100", ClampMax = "100.0", UIMin = "-100", UIMax = "100.0"))
  float Longitude = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "-10", ClampMax = "10", UIMin = "-10", UIMax = "10"))
  float Timezone = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "0.0", ClampMax = "100.0", UIMin = "0.0", UIMax = "100.0"))
  float RoadSnowiness = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "0.0", ClampMax = "12.0", UIMin = "0.0", UIMax = "12.0"))
  float Month = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "0.0", ClampMax = "31.0", UIMin = "0.0", UIMax = "31.0"))
  float Day = 0.0f;

  UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (ClampMin = "0.0", ClampMax = "24", UIMin = "0.0", UIMax = "24.0"))
  float Time = 0.0f;

};