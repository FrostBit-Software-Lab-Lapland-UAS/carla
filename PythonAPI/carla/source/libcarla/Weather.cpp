// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// Copyright(c) 2021 FrostBit Software Lab
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include <carla/rpc/WeatherParameters.h>

#include <ostream>

namespace carla {
namespace rpc {

  std::ostream &operator<<(std::ostream &out, const WeatherParameters &weather) {
    out << "WeatherParameters(cloudiness=" << std::to_string(weather.cloudiness)
        << ", cloudiness=" << std::to_string(weather.cloudiness)
        << ", precipitation=" << std::to_string(weather.precipitation)
        << ", precipitation_deposits=" << std::to_string(weather.precipitation_deposits)
        << ", wind_intensity=" << std::to_string(weather.wind_intensity)
        << ", sun_azimuth_angle=" << std::to_string(weather.sun_azimuth_angle)
        << ", sun_altitude_angle=" << std::to_string(weather.sun_altitude_angle)
        << ", fog_density=" << std::to_string(weather.fog_density)
        << ", fog_distance=" << std::to_string(weather.fog_distance)
        << ", fog_falloff=" << std::to_string(weather.fog_falloff)
        << ", wetness=" << std::to_string(weather.wetness)
        << ", scattering_intensity=" << std::to_string(weather.scattering_intensity)
        << ", mie_scattering_scale=" << std::to_string(weather.mie_scattering_scale)
        << ", rayleigh_scattering_scale=" << std::to_string(weather.rayleigh_scattering_scale)
        << ", snow_amount=" << std::to_string(weather.snow_amount)
        << ", snow_dirtyness=" << std::to_string(weather.snow_dirtyness)
        << ", temperature=" << std::to_string(weather.temperature)
        << ", ice_amount=" << std::to_string(weather.ice_amount)
		<< ", particle_size=" << std::to_string(weather.particle_size)
		<< ", relative_humidity=" << std::to_string(weather.relative_humidity)
		<< ", dewpoint=" << std::to_string(weather.dewpoint)
        << ", wind_direction=" << std::to_string(weather.wind_direction)
        << ", latitude=" << std::to_string(weather.latitude)
        << ", longitude=" << std::to_string(weather.longitude)
        << ", timezone=" << std::to_string(weather.timezone)
        << ", road_snowiness=" << std::to_string(weather.road_snowiness)
        << ", month=" << std::to_string(weather.month)
        << ", day=" << std::to_string(weather.day)
        << ", time=" << std::to_string(weather.time) << ')';
    return out;
  }

} // namespace rpc
} // namespace carla

void export_weather() {
  using namespace boost::python;
  namespace cr = carla::rpc;

  auto cls = class_<cr::WeatherParameters>("WeatherParameters")

	  // Boost python cannot take more than 15 arguments, so this is disabled
      /*.def(init<float, float, float, float, float, float, float, float, float, float, float, float, float, float>(
        (arg("cloudiness")=0.0f,
         arg("precipitation")=0.0f,
         arg("precipitation_deposits")=0.0f,
         arg("wind_intensity")=0.0f,
         arg("sun_azimuth_angle")=0.0f,
         arg("sun_altitude_angle")=0.0f,
         arg("fog_density")=0.0f,
         arg("fog_distance")=0.0f,
         arg("fog_falloff")=0.0f,
         arg("wetness")=0.0f,
         arg("scattering_intensity")=0.0f,
         arg("mie_scattering_scale")=0.0f,
         arg("rayleigh_scattering_scale")=0.0331f,
         arg("snow_amount")=0.0f,
         arg("temperature")=0.0f,
         arg("ice_amount")=0.0f,
         arg("particle_size")=0.0f)))*/
    .def_readwrite("cloudiness", &cr::WeatherParameters::cloudiness)
    .def_readwrite("precipitation", &cr::WeatherParameters::precipitation)
    .def_readwrite("precipitation_deposits", &cr::WeatherParameters::precipitation_deposits)
    .def_readwrite("wind_intensity", &cr::WeatherParameters::wind_intensity)
    .def_readwrite("sun_azimuth_angle", &cr::WeatherParameters::sun_azimuth_angle)
    .def_readwrite("sun_altitude_angle", &cr::WeatherParameters::sun_altitude_angle)
    .def_readwrite("fog_density", &cr::WeatherParameters::fog_density)
    .def_readwrite("fog_distance", &cr::WeatherParameters::fog_distance)
    .def_readwrite("fog_falloff", &cr::WeatherParameters::fog_falloff)
    .def_readwrite("wetness", &cr::WeatherParameters::wetness)
    .def_readwrite("scattering_intensity", &cr::WeatherParameters::scattering_intensity)
    .def_readwrite("mie_scattering_scale", &cr::WeatherParameters::mie_scattering_scale)
    .def_readwrite("rayleigh_scattering_scale", &cr::WeatherParameters::rayleigh_scattering_scale)
    .def_readwrite("snow_amount", &cr::WeatherParameters::snow_amount)
    .def_readwrite("snow_dirtyness", &cr::WeatherParameters::snow_dirtyness)
    .def_readwrite("temperature", &cr::WeatherParameters::temperature)
    .def_readwrite("ice_amount", &cr::WeatherParameters::ice_amount)
    .def_readwrite("particle_size", &cr::WeatherParameters::particle_size)
	.def_readwrite("relative_humidity", &cr::WeatherParameters::relative_humidity)
	.def_readwrite("dewpoint", &cr::WeatherParameters::dewpoint)
    .def_readwrite("wind_direction", &cr::WeatherParameters::wind_direction)
    .def_readwrite("latitude", &cr::WeatherParameters::latitude)
    .def_readwrite("longitude", &cr::WeatherParameters::longitude)
    .def_readwrite("timezone", &cr::WeatherParameters::timezone)
    .def_readwrite("road_snowiness", &cr::WeatherParameters::road_snowiness)
    .def_readwrite("month", &cr::WeatherParameters::month)
    .def_readwrite("day", &cr::WeatherParameters::day)
    .def_readwrite("time", &cr::WeatherParameters::time)
    .def("__eq__", &cr::WeatherParameters::operator==)
    .def("__ne__", &cr::WeatherParameters::operator!=)
    .def(self_ns::str(self_ns::self));

  cls.attr("Default") = cr::WeatherParameters::Default;
  cls.attr("ClearNoon") = cr::WeatherParameters::ClearNoon;
  cls.attr("CloudyNoon") = cr::WeatherParameters::CloudyNoon;
  cls.attr("WetNoon") = cr::WeatherParameters::WetNoon;
  cls.attr("WetCloudyNoon") = cr::WeatherParameters::WetCloudyNoon;
  cls.attr("MidRainyNoon") = cr::WeatherParameters::MidRainyNoon;
  cls.attr("HardRainNoon") = cr::WeatherParameters::HardRainNoon;
  cls.attr("SoftRainNoon") = cr::WeatherParameters::SoftRainNoon;
  cls.attr("ClearSunset") = cr::WeatherParameters::ClearSunset;
  cls.attr("CloudySunset") = cr::WeatherParameters::CloudySunset;
  cls.attr("WetSunset") = cr::WeatherParameters::WetSunset;
  cls.attr("WetCloudySunset") = cr::WeatherParameters::WetCloudySunset;
  cls.attr("MidRainSunset") = cr::WeatherParameters::MidRainSunset;
  cls.attr("HardRainSunset") = cr::WeatherParameters::HardRainSunset;
  cls.attr("SoftRainSunset") = cr::WeatherParameters::SoftRainSunset;

  cls.attr("WinterClearMorning") = cr::WeatherParameters::WinterClearMorning;
  cls.attr("WinterClearNoon") = cr::WeatherParameters::WinterClearNoon;
  cls.attr("WinterWetNoon") = cr::WeatherParameters::WinterWetNoon;
  cls.attr("WinterCloudyNoon") = cr::WeatherParameters::WinterCloudyNoon;
  cls.attr("WinterClearNight") = cr::WeatherParameters::WinterClearNight;
  cls.attr("WinterSoftSnowNoon") = cr::WeatherParameters::WinterSoftSnowNoon;
  cls.attr("WinterMidSnowNoon") = cr::WeatherParameters::WinterMidSnowNoon;
  cls.attr("WinterHardSnowNoon") = cr::WeatherParameters::WinterHardSnowNoon;
  cls.attr("WinterSoftSnowMorning") = cr::WeatherParameters::WinterSoftSnowMorning;
  cls.attr("WinterMidSnowMorning") = cr::WeatherParameters::WinterMidSnowMorning;
  cls.attr("WinterHardSnowMorning") = cr::WeatherParameters::WinterHardSnowMorning;
}
