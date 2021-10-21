import concurrent.futures
import grpc
import logging
import queue
import time

import model_pb2
import model_pb2_grpc


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)


class CustomCollatorImpl(model_pb2_grpc.CustomCollatorServicer):
    def __init__(self):
        # for collecting multiple input messages
        self.inputs = 2
        self.in_queues = [
            queue.Queue(maxsize=1)
            for i in range(0, self.inputs)
        ]

    def ImageInput(self, request_iterator, context):
        # collect image inputs
        for message in request_iterator:
            # put message if queue is empty, else discard message and write a warning
            try:
                self.in_queues[0].put(message, block=False)
            except queue.Full:
                logging.warning("dropped ImageInput message (queue full)")
                pass

    def DetectedObjectsInput(self, request_iterator, context):
        for message in request_iterator:
            # put message if queue is empty, else discard message and write a warning
            try:
                self.in_queues[1].put(message, block=False)
            except queue.Full:
                logging.info("dropped DetectedObjectsInput message (queue full)")

    def CombinedOutput(self, request, context):
        while True:
            inputs = [None for i in range(0, self.inputs)]
            # get the next object from each queue, wait if there is no object
            for i in range(0, self.inputs):
                inputs[i] = self.in_queues[i].get()

            # combine the messages and send them to the output stream
            yield model_pb2.ImageWithObjects(
                image=inputs[0],
                objects=inputs[1]
            )


grpcserver = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
model_pb2_grpc.add_CustomCollatorServicer_to_server(CustomCollatorImpl(), grpcserver)
grpcserver.add_insecure_port('0.0.0.0:8061')
grpcserver.start()

while True:
    time.sleep(1)
