// Copyright (c) 2020 Computer Vision Center (CVC) at the Universitat Autonoma
// de Barcelona (UAB).
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include "carla/sensor/s11n/CustomSemanticLidarSerializer.h"
#include "carla/sensor/data/CustomSemanticLidarMeasurement.h"

namespace carla {
namespace sensor {
namespace s11n {

  SharedPtr<SensorData> CustomSemanticLidarSerializer::Deserialize(RawData &&data) {
    return SharedPtr<data::CustomSemanticLidarMeasurement>(
        new data::CustomSemanticLidarMeasurement{std::move(data)});
  }

} // namespace s11n
} // namespace sensor
} // namespace carla
