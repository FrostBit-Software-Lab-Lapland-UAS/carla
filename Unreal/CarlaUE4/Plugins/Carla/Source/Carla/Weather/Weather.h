// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// Copyright(c) 2021 FrostBit Software Lab
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include "GameFramework/Actor.h"
#include "Carla/Weather/WeatherParameters.h"
#include "Weather.generated.h"

UCLASS(Abstract)
class CARLA_API AWeather : public AActor
{
  GENERATED_BODY()

public:

  AWeather(const FObjectInitializer& ObjectInitializer);

  /// Update the weather parameters and notifies it to the blueprint's event
  UFUNCTION(BlueprintCallable)
  void ApplyWeather(const FWeatherParameters &WeatherParameters);

  UFUNCTION(BlueprintCallable)
  void UpdateRoad(bool enabled);

  /// Notifing the weather to the blueprint's event
  void NotifyWeather();

  /// Update the weather parameters without notifing it to the blueprint's event
  UFUNCTION(BlueprintCallable)
  void SetWeather(const FWeatherParameters &WeatherParameters);

  /// Returns the current WeatherParameters
  UFUNCTION(BlueprintCallable)
  const FWeatherParameters &GetCurrentWeather() const
  {
    return Weather;
  }

  UFUNCTION(BlueprintImplementableEvent, BlueprintCallable, Category = Gameplay)
  void SetStaticTiretracks(bool enabled);

protected:

  UFUNCTION(BlueprintImplementableEvent)
  void RefreshWeather(const FWeatherParameters &WeatherParameters);

private:

  UPROPERTY(VisibleAnywhere)
  FWeatherParameters Weather;
};
