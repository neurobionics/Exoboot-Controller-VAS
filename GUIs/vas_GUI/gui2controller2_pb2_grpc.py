# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import gui2controller2_pb2 as gui2controller2__pb2


class CommunicationServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GUI_Messenger = channel.unary_unary(
                '/CommunicationService/GUI_Messenger',
                request_serializer=gui2controller2__pb2.data_stream.SerializeToString,
                response_deserializer=gui2controller2__pb2.Null.FromString,
                )

class CommunicationServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GUI_Messenger(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_CommunicationServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GUI_Messenger': grpc.unary_unary_rpc_method_handler(
                    servicer.GUI_Messenger,
                    request_deserializer=gui2controller2__pb2.data_stream.FromString,
                    response_serializer=gui2controller2__pb2.Null.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'CommunicationService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class CommunicationService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GUI_Messenger(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/CommunicationService/GUI_Messenger',
            gui2controller2__pb2.data_stream.SerializeToString,
            gui2controller2__pb2.Null.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
