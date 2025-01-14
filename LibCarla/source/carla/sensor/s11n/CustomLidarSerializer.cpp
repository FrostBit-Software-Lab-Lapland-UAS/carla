// Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.


#include "carla/sensor/data/CustomLidarMeasurement.h"
#include "carla/sensor/s11n/CustomLidarSerializer.h"

namespace carla {
namespace sensor {
namespace s11n {

  SharedPtr<SensorData> CustomLidarSerializer::Deserialize(RawData &&data) {
    return SharedPtr<data::CustomLidarMeasurement>(
        new data::CustomLidarMeasurement{std::move(data)});
  }

} // namespace s11n
} // namespace sensor
} // namespace carla
