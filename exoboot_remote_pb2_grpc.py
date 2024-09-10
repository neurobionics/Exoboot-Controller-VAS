# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import exoboot_remote_pb2 as exoboot__remote__pb2

GRPC_GENERATED_VERSION = '1.64.1'
GRPC_VERSION = grpc.__version__
EXPECTED_ERROR_RELEASE = '1.65.0'
SCHEDULED_RELEASE_DATE = 'June 25, 2024'
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    warnings.warn(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in exoboot_remote_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
        + f' This warning will become an error in {EXPECTED_ERROR_RELEASE},'
        + f' scheduled for release on {SCHEDULED_RELEASE_DATE}.',
        RuntimeWarning
    )


class exoboot_over_networkStub(object):
    """GRPC Service
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.testconnection = channel.unary_unary(
                '/exoboot_over_network/testconnection',
                request_serializer=exoboot__remote__pb2.testmsg.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)
        self.get_startstamp = channel.unary_unary(
                '/exoboot_over_network/get_startstamp',
                request_serializer=exoboot__remote__pb2.null.SerializeToString,
                response_deserializer=exoboot__remote__pb2.startstamp.FromString,
                _registered_method=True)
        self.get_subject_info = channel.unary_unary(
                '/exoboot_over_network/get_subject_info',
                request_serializer=exoboot__remote__pb2.null.SerializeToString,
                response_deserializer=exoboot__remote__pb2.subject_info.FromString,
                _registered_method=True)
        self.chop = channel.unary_unary(
                '/exoboot_over_network/chop',
                request_serializer=exoboot__remote__pb2.beaver.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)
        self.set_pause = channel.unary_unary(
                '/exoboot_over_network/set_pause',
                request_serializer=exoboot__remote__pb2.pause.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)
        self.set_quit = channel.unary_unary(
                '/exoboot_over_network/set_quit',
                request_serializer=exoboot__remote__pb2.quit.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)
        self.set_torque = channel.unary_unary(
                '/exoboot_over_network/set_torque',
                request_serializer=exoboot__remote__pb2.torques.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)
        self.call = channel.unary_unary(
                '/exoboot_over_network/call',
                request_serializer=exoboot__remote__pb2.result.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)
        self.question = channel.unary_unary(
                '/exoboot_over_network/question',
                request_serializer=exoboot__remote__pb2.survey.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)
        self.slider_update = channel.unary_unary(
                '/exoboot_over_network/slider_update',
                request_serializer=exoboot__remote__pb2.slider.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)
        self.presentation_result = channel.unary_unary(
                '/exoboot_over_network/presentation_result',
                request_serializer=exoboot__remote__pb2.presentation.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)
        self.comparison_result = channel.unary_unary(
                '/exoboot_over_network/comparison_result',
                request_serializer=exoboot__remote__pb2.comparison.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)
        self.pref_result = channel.unary_unary(
                '/exoboot_over_network/pref_result',
                request_serializer=exoboot__remote__pb2.preference.SerializeToString,
                response_deserializer=exoboot__remote__pb2.receipt.FromString,
                _registered_method=True)


class exoboot_over_networkServicer(object):
    """GRPC Service
    """

    def testconnection(self, request, context):
        """General Methods
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def get_startstamp(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def get_subject_info(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def chop(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def set_pause(self, request, context):
        """Exoboot Controller Commands
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def set_quit(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def set_torque(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def call(self, request, context):
        """Vickrey Auction Specific
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def question(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def slider_update(self, request, context):
        """VAS Specific
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def presentation_result(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def comparison_result(self, request, context):
        """JND Specific
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def pref_result(self, request, context):
        """Pref Specific
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_exoboot_over_networkServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'testconnection': grpc.unary_unary_rpc_method_handler(
                    servicer.testconnection,
                    request_deserializer=exoboot__remote__pb2.testmsg.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
            'get_startstamp': grpc.unary_unary_rpc_method_handler(
                    servicer.get_startstamp,
                    request_deserializer=exoboot__remote__pb2.null.FromString,
                    response_serializer=exoboot__remote__pb2.startstamp.SerializeToString,
            ),
            'get_subject_info': grpc.unary_unary_rpc_method_handler(
                    servicer.get_subject_info,
                    request_deserializer=exoboot__remote__pb2.null.FromString,
                    response_serializer=exoboot__remote__pb2.subject_info.SerializeToString,
            ),
            'chop': grpc.unary_unary_rpc_method_handler(
                    servicer.chop,
                    request_deserializer=exoboot__remote__pb2.beaver.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
            'set_pause': grpc.unary_unary_rpc_method_handler(
                    servicer.set_pause,
                    request_deserializer=exoboot__remote__pb2.pause.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
            'set_quit': grpc.unary_unary_rpc_method_handler(
                    servicer.set_quit,
                    request_deserializer=exoboot__remote__pb2.quit.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
            'set_torque': grpc.unary_unary_rpc_method_handler(
                    servicer.set_torque,
                    request_deserializer=exoboot__remote__pb2.torques.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
            'call': grpc.unary_unary_rpc_method_handler(
                    servicer.call,
                    request_deserializer=exoboot__remote__pb2.result.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
            'question': grpc.unary_unary_rpc_method_handler(
                    servicer.question,
                    request_deserializer=exoboot__remote__pb2.survey.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
            'slider_update': grpc.unary_unary_rpc_method_handler(
                    servicer.slider_update,
                    request_deserializer=exoboot__remote__pb2.slider.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
            'presentation_result': grpc.unary_unary_rpc_method_handler(
                    servicer.presentation_result,
                    request_deserializer=exoboot__remote__pb2.presentation.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
            'comparison_result': grpc.unary_unary_rpc_method_handler(
                    servicer.comparison_result,
                    request_deserializer=exoboot__remote__pb2.comparison.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
            'pref_result': grpc.unary_unary_rpc_method_handler(
                    servicer.pref_result,
                    request_deserializer=exoboot__remote__pb2.preference.FromString,
                    response_serializer=exoboot__remote__pb2.receipt.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'exoboot_over_network', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('exoboot_over_network', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class exoboot_over_network(object):
    """GRPC Service
    """

    @staticmethod
    def testconnection(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/testconnection',
            exoboot__remote__pb2.testmsg.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def get_startstamp(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/get_startstamp',
            exoboot__remote__pb2.null.SerializeToString,
            exoboot__remote__pb2.startstamp.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def get_subject_info(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/get_subject_info',
            exoboot__remote__pb2.null.SerializeToString,
            exoboot__remote__pb2.subject_info.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def chop(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/chop',
            exoboot__remote__pb2.beaver.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def set_pause(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/set_pause',
            exoboot__remote__pb2.pause.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def set_quit(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/set_quit',
            exoboot__remote__pb2.quit.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def set_torque(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/set_torque',
            exoboot__remote__pb2.torques.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def call(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/call',
            exoboot__remote__pb2.result.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def question(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/question',
            exoboot__remote__pb2.survey.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def slider_update(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/slider_update',
            exoboot__remote__pb2.slider.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def presentation_result(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/presentation_result',
            exoboot__remote__pb2.presentation.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def comparison_result(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/comparison_result',
            exoboot__remote__pb2.comparison.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def pref_result(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/exoboot_over_network/pref_result',
            exoboot__remote__pb2.preference.SerializeToString,
            exoboot__remote__pb2.receipt.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
