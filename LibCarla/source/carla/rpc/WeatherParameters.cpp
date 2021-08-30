// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// Copyright(c) 2021 FrostBit Software Lab
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include "carla/rpc/WeatherParameters.h"

namespace carla {
namespace rpc {

  using WP = WeatherParameters;

  //                        cloudiness,   precip.  prec.dep.     wind,   azimuth,   altitude,  fog dens,  fog dist,  fog fall,  wetness,							snow,   temp,  iciness, psize, r_humidity, dewpoint, wind dir

  WP WP::Default         = {     -1.0f,    -1.0f,     -1.0f,  -1.00f,    -1.0f,      -1.0f,    -1.0f,     -1.0f,     -1.0f,   -1.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  85.0f, 0.0f, 15.0f   };
  WP WP::ClearNoon       = {     15.0f,     0.0f,      0.0f,   0.35f,     0.0f,      75.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  84.0f, 0.0f, 35.0f   };
  WP WP::CloudyNoon      = {     80.0f,     0.0f,      0.0f,   0.35f,     0.0f,      75.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  88.0f, 0.0f, 65.0f   };
  WP WP::WetNoon         = {     20.0f,     0.0f,     50.0f,   0.35f,     0.0f,      75.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  88.0f, 0.0f, 95.0f   };
  WP WP::WetCloudyNoon   = {     80.0f,     0.0f,     50.0f,   0.35f,     0.0f,      75.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  88.0f, 0.0f, 115.0f  };
  WP WP::MidRainyNoon    = {     80.0f,    30.0f,     50.0f,   0.40f,     0.0f,      75.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  84.0f, 0.0f, 135.0f  };
  WP WP::HardRainNoon    = {     90.0f,    60.0f,    100.0f,   1.00f,     0.0f,      75.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  81.0f, 0.0f, 155.0f  };
  WP WP::SoftRainNoon    = {     70.0f,    15.0f,     50.0f,   0.35f,     0.0f,      75.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  75.0f, 0.0f, 185.0f  };
  WP WP::ClearSunset     = {     15.0f,     0.0f,      0.0f,   0.35f,     0.0f,      15.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  77.0f, 0.0f, 191.0f  };
  WP WP::CloudySunset    = {     80.0f,     0.0f,      0.0f,   0.35f,     0.0f,      15.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  88.0f, 0.0f, 200.0f  };
  WP WP::WetSunset       = {     20.0f,     0.0f,     50.0f,   0.35f,     0.0f,      15.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  88.0f, 0.0f, 202.0f  };
  WP WP::WetCloudySunset = {     90.0f,     0.0f,     50.0f,   0.35f,     0.0f,      15.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  88.0f, 0.0f, 13.0f   };
  WP WP::MidRainSunset   = {     80.0f,    30.0f,     50.0f,   0.40f,     0.0f,      15.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  88.0f, 0.0f, 75.0f   };
  WP WP::HardRainSunset  = {     80.0f,    60.0f,    100.0f,   1.00f,     0.0f,      15.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  88.0f, 0.0f, 43.0f   };
  WP WP::SoftRainSunset  = {     90.0f,    15.0f,     50.0f,   0.35f,     0.0f,      15.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,    20.0f,  0.0f,   0.0f,  88.0f, 0.0f, 55.0f   };
 
  WP WP::WinterMorning   = {      0.0f,     0.0f,     20.0f,   0.18f,     270.0f,     2.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,  100.0f,   -9.4f,  0.0f,   1.5f,  88.0f, -19.1f,  115.0f };
  WP WP::WinterNoon      = {      0.0f,     0.0f,     20.0f,   0.18f,     270.0f,    75.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,  98.0f,   -14.4f,  0.0f,   1.5f,  88.0f, -19.1f,  75.0f  };
  WP WP::WinterCloudyNoon= {    100.0f,     0.0f,     20.0f,   0.50f,     270.0f,    75.0f,    29.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,  95.0f,   -17.4f,  0.0f,   3.5f,  88.0f, -19.1f,  55.0f  };
  WP WP::WinterNight     = {      0.0f,     0.0f,     20.0f,   0.05f,     270.0f,    -8.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,  100.0f,   -21.4f,  0.0f,   7.0f,  88.0f, -19.1f, 95.0f };
  WP WP::SoftSnowNoon    = {    100.0f,    20.0f,     10.0f,   0.10f,     270.0f,    75.0f,    10.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,   77.0f,   -17.4f,  0.0f,   5.0f,  88.0f, -19.1f, 35.0f };
  WP WP::MidSnowNoon     = {    100.0f,    44.0f,     34.0f,   1.00f,     270.0f,    75.0f,    20.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,   91.0f,   -17.4f,  0.0f,   0.5f,  88.0f, -19.1f, 75.0f };
  WP WP::HardSnowNoon    = {    100.0f,    80.0f,     80.0f,   0.35f,     270.0f,    75.0f,    23.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,  99.0f,   -16.4f,  0.0f,   2.0f,  88.0f, -19.1f,  25.0f  };
  WP WP::SoftSnowMorning = {     20.0f,    20.0f,     20.0f,   0.18f,     270.0f,     2.0f,     0.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,   85.0f,   -15.4f,  0.0f,   1.5f,  88.0f, -19.1f, 115.0f};
  WP WP::MidSnowMorning  = {     40.0f,    51.0f,     40.0f,   0.35f,     270.0f,     2.0f,     4.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,   89.0f,   -19.4f,  0.0f,   4.0f,  88.0f, -19.1f, 45.0f };
  WP WP::HardSnowMorning = {    100.0f,    82.0f,     82.0f,   0.20f,     270.0f,     2.0f,    12.0f,      0.0f,      0.0f,    0.0f,  1.0f,   0.03f,   0.0331f,  71.0f,   -13.4f,  0.0f,   4.5f,  88.0f, -19.1f,  87.0f  };

} // namespace rpc
} // namespace carla