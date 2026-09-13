import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import Float32


class ProcessingNode(Node):
    def __init__(self):
        super().__init__('processing_node')
        self.declare_parameter('threshold', 0.5)
        self.count_above = 0
        self.sub = self.create_subscription(
            Float32, 'sensor_data', self.on_data, 10
        )
        self.pub = self.create_publisher(Float32, 'processed_data', 10)
        self.add_on_set_parameters_callback(self.on_param)

    def on_param(self, params):
        for p in params:
            if p.name == 'threshold' and p.value < 0.0:
                return SetParametersResult(
                    successful=False, reason='threshold must be >= 0'
                )
        return SetParametersResult(successful=True)

    def on_data(self, msg):
        th = self.get_parameter('threshold').value
        if abs(msg.data) > th:
            self.count_above += 1
            self.pub.publish(msg)


def main():
    rclpy.init()
    node = ProcessingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
