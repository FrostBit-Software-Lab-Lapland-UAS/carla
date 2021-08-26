// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// Copyright(c) 2021 FrostBit Software Lab
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#pragma once

#include "carla/MsgPack.h"

#ifdef LIBCARLA_INCLUDED_FROM_UE4
#  include "Carla/Weather/WeatherParameters.h"
#endif // LIBCARLA_INCLUDED_FROM_UE4

namespace carla {
namespace rpc {

  class WeatherParameters {
  public:

    /// @name Weather presets
    /// @{

    static WeatherParameters Default;
    static WeatherParameters ClearNoon;
    static WeatherParameters CloudyNoon;
    static WeatherParameters WetNoon;
    static WeatherParameters WetCloudyNoon;
    static WeatherParameters MidRainyNoon;
    static WeatherParameters HardRainNoon;
    static WeatherParameters SoftRainNoon;
    static WeatherParameters ClearSunset;
    static WeatherParameters CloudySunset;
    static WeatherParameters WetSunset;
    static WeatherParameters WetCloudySunset;
    static WeatherParameters MidRainSunset;
    static WeatherParameters HardRainSunset;
    static WeatherParameters SoftRainSunset;
    static WeatherParameters ClearNight;
    static WeatherParameters CloudyNight;
    static WeatherParameters WetNight;
    static WeatherParameters WetCloudyNight;
    static WeatherParameters SoftRainNight;
    static WeatherParameters MidRainyNight;
    static WeatherParameters HardRainNight;

    static WeatherParameters WinterMorning;
    static WeatherParameters WinterNoon;
    static WeatherParameters WinterCloudyNoon;
    static WeatherParameters WinterNight;
    static WeatherParameters SoftSnowNoon;    
    static WeatherParameters MidSnowNoon;
    static WeatherParameters HardSnowNoon;
    static WeatherParameters SoftSnowMorning;
    static WeatherParameters MidSnowMorning;
    static WeatherParameters HardSnowMorning;

    /// @}

    WeatherParameters() = default;

    WeatherParameters(
        float in_cloudiness,
        float in_precipitation,
        float in_precipitation_deposits,
        float in_wind_intensity,
        float in_sun_azimuth_angle,
        float in_sun_altitude_angle,
        float in_fog_density,
        float in_fog_distance,
        float in_fog_falloff,
        float in_wetness,
        float in_scattering_intensity,
        float in_mie_scattering_scale,
        float in_rayleigh_scattering_scale,
        float in_snow_amount,
        float in_temperature,
        float in_ice_amount,
        float in_particle_size,
		float in_relative_humidity,
		float in_dewpoint,
        float in_wind_direction)
      : cloudiness(in_cloudiness),
        precipitation(in_precipitation),
        precipitation_deposits(in_precipitation_deposits),
        wind_intensity(in_wind_intensity),
        sun_azimuth_angle(in_sun_azimuth_angle),
        sun_altitude_angle(in_sun_altitude_angle),
        fog_density(in_fog_density),
        fog_distance(in_fog_distance),
        fog_falloff(in_fog_falloff),
        wetness(in_wetness),
        scattering_intensity(in_scattering_intensity),
        mie_scattering_scale(in_mie_scattering_scale),
        rayleigh_scattering_scale(in_rayleigh_scattering_scale), 
        snow_amount(in_snow_amount),
        temperature(in_temperature),
        ice_amount(in_ice_amount),
        particle_size(in_particle_size),
		relative_humidity(in_relative_humidity),
		dewpoint(in_dewpoint),
        wind_direction(in_wind_direction) {}

    float cloudiness = 0.0f;
    float precipitation = 0.0f;
    float precipitation_deposits = 0.0f;
    float wind_intensity = 0.0f;
    float sun_azimuth_angle = 0.0f;
    float sun_altitude_angle = 0.0f;
    float fog_density = 0.0f;
    float fog_distance = 0.0f;
    float fog_falloff = 0.0f;
    float wetness = 0.0f;
    float scattering_intensity = 0.0f;
    float mie_scattering_scale = 0.0f;
    float rayleigh_scattering_scale = 0.0331f;
    float snow_amount = 0.0f;
    float temperature = 0.0f;
    float ice_amount = 0.0f;
    float particle_size = 0.0f;
	float relative_humidity = 0.0f;
	float dewpoint = 0.0f;
    float wind_direction = 0.0f;

#ifdef LIBCARLA_INCLUDED_FROM_UE4

    WeatherParameters(const FWeatherParameters &Weather)
      : cloudiness(Weather.Cloudiness),
        precipitation(Weather.Precipitation),
        precipitation_deposits(Weather.PrecipitationDeposits),
        wind_intensity(Weather.WindIntensity),
        sun_azimuth_angle(Weather.SunAzimuthAngle),
        sun_altitude_angle(Weather.SunAltitudeAngle),
        fog_density(Weather.FogDensity),
        fog_distance(Weather.FogDistance),
        fog_falloff(Weather.FogFalloff),
        wetness(Weather.Wetness),
        scattering_intensity(Weather.ScatteringIntensity),
        mie_scattering_scale(Weather.MieScatteringScale),
        rayleigh_scattering_scale(Weather.RayleighScatteringScale),
        snow_amount(Weather.SnowAmount),
        temperature(Weather.Temperature),
        ice_amount(Weather.IceAmount),
        particle_size(Weather.ParticleSize),
		relative_humidity(Weather.RelativeHumidity),
		dewpoint(Weather.Dewpoint),
        wind_direction(Weather.WindDirection) {}

    operator FWeatherParameters() const {
      FWeatherParameters Weather;
      Weather.Cloudiness = cloudiness;
      Weather.Precipitation = precipitation;
      Weather.PrecipitationDeposits = precipitation_deposits;
      Weather.WindIntensity = wind_intensity;
      Weather.SunAzimuthAngle = sun_azimuth_angle;
      Weather.SunAltitudeAngle = sun_altitude_angle;
      Weather.FogDensity = fog_density;
      Weather.FogDistance = fog_distance;
      Weather.FogFalloff = fog_falloff;
      Weather.Wetness = wetness;
      Weather.ScatteringIntensity = scattering_intensity;
      Weather.MieScatteringScale = mie_scattering_scale;
      Weather.RayleighScatteringScale = rayleigh_scattering_scale;
      Weather.SnowAmount = snow_amount;
      Weather.Temperature = temperature;
      Weather.IceAmount = ice_amount;
      Weather.ParticleSize = particle_size;
	  Weather.RelativeHumidity = relative_humidity;
	  Weather.Dewpoint = dewpoint;
      Weather.WindDirection = wind_direction;
      return Weather;
    }

#endif // LIBCARLA_INCLUDED_FROM_UE4

    bool operator!=(const WeatherParameters &rhs) const {
		return
			cloudiness != rhs.cloudiness ||
			precipitation != rhs.precipitation ||
			precipitation_deposits != rhs.precipitation_deposits ||
			wind_intensity != rhs.wind_intensity ||
			sun_azimuth_angle != rhs.sun_azimuth_angle ||
			sun_altitude_angle != rhs.sun_altitude_angle ||
			fog_density != rhs.fog_density ||
			fog_distance != rhs.fog_distance ||
			fog_falloff != rhs.fog_falloff ||
			wetness != rhs.wetness ||
            scattering_intensity != rhs.scattering_intensity ||
            mie_scattering_scale != rhs.mie_scattering_scale ||
            rayleigh_scattering_scale != rhs.rayleigh_scattering_scale ||
			snow_amount != rhs.snow_amount ||
			temperature != rhs.temperature ||
			ice_amount != rhs.ice_amount ||
			particle_size != rhs.particle_size ||
			relative_humidity != rhs.relative_humidity ||
			dewpoint != rhs.dewpoint ||
            wind_direction != rhs.wind_direction;
    }

    bool operator==(const WeatherParameters &rhs) const {
      return !(*this != rhs);
    }

    MSGPACK_DEFINE_ARRAY(
        cloudiness,
        precipitation,
        precipitation_deposits,
        wind_intensity,
        sun_azimuth_angle,
        sun_altitude_angle,
        fog_density,
        fog_distance,
        fog_falloff,
        wetness,
        scattering_intensity,
        mie_scattering_scale,
        rayleigh_scattering_scale,
        snow_amount,
        temperature,
        ice_amount,
        particle_size,
		relative_humidity,
		dewpoint,
        wind_direction);
  };

} // namespace rpc
} // namespace carla