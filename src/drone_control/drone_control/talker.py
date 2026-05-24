import rclpy
from rclpy.node import Node

class Talker(Node):
    def __init__(self):
        super().__init__('talker')
        self.get_logger().info("Hello ROS2")

def main(args=None):
    rclpy.init(args=args)
    node = Talker()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
