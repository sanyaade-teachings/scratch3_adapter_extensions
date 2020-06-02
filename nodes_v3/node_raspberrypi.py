'''
pip install gpiozero pigpio --user
# docs: https://gpiozero.readthedocs.io/en/stable/remote_gpio.html
'''
import contextlib
import os  # env
import sys
import time
from io import StringIO
from time import sleep

from loguru import logger

from codelab_adapter_client import AdapterNode
from codelab_adapter_client.utils import get_or_create_node_logger_dir, install_requirement

# GPIOZERO_PIN_FACTORY=pigpio PIGPIO_ADDR= "raspberrypi.local"# 192.168.1.3
# os.environ["GPIOZERO_PIN_FACTORY"] = "pigpio"
# os.environ["PIGPIO_ADDR"] = "raspberrypi.local"

node_logger_dir = get_or_create_node_logger_dir()
debug_log = str(node_logger_dir / "debug.log")
logger.add(debug_log, rotation="1 MB", level="DEBUG")


class RPINode(AdapterNode):
    NODE_ID = "eim/node_raspberrypi"
    REQUIREMENTS = ["gpiozero", "pigpio"]

    def __init__(self):
        super().__init__(logger=logger)

    def _import_requirement_or_import(self):
        requirement = self.REQUIREMENTS
        try:
            import gpiozero, pigpio
        except ModuleNotFoundError:
            self.pub_notification(f'try to install {" ".join(requirement)}...')
            install_requirement(requirement)
            self.pub_notification(f'{" ".join(requirement)} installed!')
        from gpiozero import LED
        from gpiozero.pins.pigpio import PiGPIOFactory
        global LED, PiGPIOFactory

    def run_python_code(self, code):
        try:
            output = eval(code, {"__builtins__": None}, {
                "led": self.led,
                "factory": self.factory
            })
        except Exception as e:
            output = e
        return output

    def extension_message_handle(self, topic, payload):
        self.logger.info(f'code: {payload["content"]}')
        message_id = payload.get("message_id")
        python_code = payload["content"]
        output = self.run_python_code(python_code)
        payload["content"] = str(output)
        message = {"payload": payload}
        self.publish(message)

    def run(self):
        "避免插件结束退出"
        self._import_requirement_or_import()
        self.factory = PiGPIOFactory(host='raspberrypi.local')  # 192.168.1.3
        # 连接成功
        if self.factory:
            # 反馈 连接成功。 失败将弹出通知
            self.pub_notification("Pi Connected!", type="SUCCESS")
        
        self.led = LED(17, pin_factory=self.factory)
        while self._running:
            time.sleep(0.5)


if __name__ == "__main__":
    try:
        node = RPINode()
        node.receive_loop_as_thread()
        node.run()
    except KeyboardInterrupt:
        # node.logger.debug("KeyboardInterrupt") # work mac
        if node._running:
            node.terminate()  # Clean up before exiting.