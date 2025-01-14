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

  //                        cloudiness,   precip.  prec.dep.     wind,   azimuth,   altitude,  fog dens,  fog dist,  fog fall,  wetness,                               snow,  snow_dirtyness,     temp,  iciness,  psize, r_humidity,    dewpoint,   wind dir,         lat,       long,  timezone,  road snow,  month,    day,   time            
																																																																			     
  WP WP::Default         = {     -1.0f,    -1.0f,     -1.0f,   -1.00f,     -1.0f,      -1.0f,     -1.0f,     -1.0f,     -1.0f,    -1.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,    20.0f,     0.0f,   0.0f,      85.0f,        0.0f,      15.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::ClearNoon       = {     15.0f,     0.0f,      0.0f,    0.35f,      0.0f,      75.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,  20.0f,     0.0f,   0.0f,      84.0f,        0.0f,      35.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::CloudyNoon      = {     80.0f,     0.0f,      0.0f,    0.35f,      0.0f,      75.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,  20.0f,     0.0f,   0.0f,      88.0f,        0.0f,      65.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::WetNoon         = {     20.0f,     0.0f,     50.0f,    0.35f,      0.0f,      75.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,    20.0f,     0.0f,   0.0f,      88.0f,        0.0f,      95.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::WetCloudyNoon   = {     80.0f,     0.0f,     50.0f,    0.35f,      0.0f,      75.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,   20.0f,     0.0f,   0.0f,      88.0f,        0.0f,     115.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::MidRainyNoon    = {     80.0f,    30.0f,     50.0f,    0.40f,      0.0f,      75.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,  20.0f,     0.0f,   0.0f,      84.0f,        0.0f,     135.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::HardRainNoon    = {     90.0f,    60.0f,    100.0f,    1.00f,      0.0f,      75.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,    20.0f,     0.0f,   0.0f,      81.0f,        0.0f,     155.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::SoftRainNoon    = {     70.0f,    15.0f,     50.0f,    0.35f,      0.0f,      75.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,    20.0f,     0.0f,   0.0f,      75.0f,        0.0f,     185.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::ClearSunset     = {     15.0f,     0.0f,      0.0f,    0.35f,      0.0f,      15.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,    20.0f,     0.0f,   0.0f,      77.0f,        0.0f,     191.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::CloudySunset    = {     80.0f,     0.0f,      0.0f,    0.35f,      0.0f,      15.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,    20.0f,     0.0f,   0.0f,      88.0f,        0.0f,     200.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::WetSunset       = {     20.0f,     0.0f,     50.0f,    0.35f,      0.0f,      15.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,   20.0f,     0.0f,   0.0f,      88.0f,        0.0f,     202.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::WetCloudySunset = {     90.0f,     0.0f,     50.0f,    0.35f,      0.0f,      15.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,    20.0f,     0.0f,   0.0f,      88.0f,        0.0f,      13.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::MidRainSunset   = {     80.0f,    30.0f,     50.0f,    0.40f,      0.0f,      15.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,    20.0f,     0.0f,   0.0f,      88.0f,        0.0f,      75.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::HardRainSunset  = {     80.0f,    60.0f,    100.0f,    1.00f,      0.0f,      15.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,    20.0f,     0.0f,   0.0f,      88.0f,        0.0f,      43.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
  WP WP::SoftRainSunset  = {     90.0f,    15.0f,     50.0f,    0.35f,      0.0f,      15.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,    0.0f,  0.0f,    20.0f,     0.0f,   0.0f,      88.0f,        0.0f,      55.0f,  67.955388f, 23.684363f,      2.0f,       0.0f,   0.0f,   7.0f,   0.0f};			
	  														  			  														 														   					    					  			 						  		      	 							      	
  WP WP::WinterClearMorning    = {      0.0f,     0.0f,      0.0f,     0.2f,    270.0f,       2.0f,     0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,  100.0f,  0.0f,   -17.4f,     0.0f,   1.0f,      88.0f,      -19.1f,     115.0f,  67.955388f, 23.684363f,      2.0f,      100.0f,   2.0f,  12.0f,   9.0f};   		  
  WP WP::WinterClearNoon       = {      0.0f,     0.0f,      0.0f,     0.0f,    270.0f,      75.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,  100.0f,  0.0f,   -17.4f,     0.0f,   1.0f,      88.0f,      -19.1f,      75.0f,  67.955388f, 23.684363f,      2.0f,      90.0f,   2.0f,  15.0f,  13.0f};
  WP WP::WinterWetNoon         = {      55.0f,     0.0f,      0.0f,     0.0f,    270.0f,      75.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,  100.0f,  0.0f,    0.0f,     0.0f,   1.0f,      88.0f,      -19.1f,      75.0f,  67.955388f, 23.684363f,      2.0f,      90.0f,   2.0f,  15.0f,  13.0f};
  WP WP::WinterCloudyNoon      = {     90.8f,     0.0f,      0.0f,     0.5f,    270.0f,      75.0f,     10.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,  100.0f,  0.0f,   -17.4f,     0.0f,   1.0f,      88.0f,      -19.1f,      75.0f,  67.955388f, 23.684363f,      2.0f,      90.0f,   2.0f,  20.0f,  13.0f};
  WP WP::WinterClearNight      = {      0.0f,     0.0f,      0.0f,     0.0f,    270.0f,      -8.0f,      0.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,  100.0f,  0.0f,   -15.5f,     0.0f,   1.0f,      88.0f,      -19.1f,      95.0f,  67.955388f, 23.684363f,      2.0f,      90.0f,   2.0f,  22.0f,   0.0f};
  WP WP::WinterSoftSnowNoon    = {     90.5f,    20.0f,     36.0f,    0.18f,    270.0f,      75.0f,     5.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,   60.0f,  0.0f,  -17.4f,     0.0f,   1.0f,      88.0f,      -19.1f,      35.0f,  67.955388f, 23.684363f,      2.0f,      65.0f,   11.0f, 15.0f,  13.0f};		  
  WP WP::WinterMidSnowNoon     = {     90.5f,    50.0f,     65.0f,    0.40f,    270.0f,      75.0f,     10.5f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,   80.0f,  0.0f,   -17.4f,     0.0f,   2.0f,      88.0f,      -19.1f,      75.0f,  67.955388f, 23.684363f,      2.0f,      90.0f,   2.0f,  16.0f,  14.0f};		  
  WP WP::WinterHardSnowNoon    = {    100.0f,   100.0f,    90.0f,    0.90f,    270.0f,      75.0f,     25.0f,      0.0f,      0.5f,     0.0f,  1.0f,   0.03f,   0.0331f,  100.0f,  0.0f,   -17.4f,     0.0f,   3.0f,      88.0f,      -19.1f,      25.0f,  67.955388f, 23.684363f,      2.0f,     100.0f,   2.0f,  14.0f,  14.0f};		  
  WP WP::WinterSoftSnowMorning = {     90.5f,    20.0f,     36.6f,    0.18f,    270.0f,       2.0f,      2.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,   70.0f,  0.0f,   -17.4f,     0.0f,   1.0f,      88.0f,      -19.1f,     115.0f,  67.955388f, 23.684363f,      2.0f,      50.0f,  11.0f,  15.0f,   9.0f};		  
  WP WP::WinterMidSnowMorning  = {     100.0f,    50.0f,     60.0f,    0.42f,    270.0f,       2.0f,      10.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,   86.0f,  0.0f,   -17.4f,     0.0f,   2.0f,      88.0f,      -19.1f,      45.0f,  67.955388f, 23.684363f,      2.0f,      60.0f,  11.0f,   6.0f,   9.0f};		  
  WP WP::WinterHardSnowMorning = {    100.0f,   75.0f,    100.0f,    0.70f,    270.0f,       2.0f,     25.0f,      0.0f,      2.0f,     0.0f,  1.0f,   0.03f,   0.0331f,  100.0f,  0.0f,   -17.4f,     0.0f,   3.0f,      88.0f,      -19.1f,      87.0f,  67.955388f, 23.684363f,      2.0f,     100.0f,  11.0f,   2.0f,  11.0f};


} // namespace rpc
} // namespace carla