# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: exoboot_remote.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14\x65xoboot_remote.proto\"#\n\x0freceipt_exoboot\x12\x10\n\x08received\x18\x01 \x01(\x08\"M\n\x0fsubject_info_eb\x12\x11\n\tsubjectID\x18\x01 \x01(\t\x12\x12\n\ntrial_type\x18\x02 \x01(\t\x12\x13\n\x0b\x64\x65scription\x18\x03 \x01(\t\"\x17\n\x05pause\x12\x0e\n\x06mybool\x18\x01 \x01(\x08\"\x16\n\x04quit\x12\x0e\n\x06mybool\x18\x01 \x01(\x08\">\n\x07torques\x12\x18\n\x10peak_torque_left\x18\x01 \x01(\x02\x12\x19\n\x11peak_torque_right\x18\x02 \x01(\x02\"\x1b\n\npoly_coefs\x12\r\n\x05\x63oefs\x18\x01 \x03(\x02\"M\n\x0ftorque_schedule\x12\r\n\x05times\x18\x01 \x03(\x02\x12\x0f\n\x07torques\x18\x02 \x03(\x02\x12\x1a\n\x05\x63oefs\x18\x03 \x03(\x0b\x32\x0b.poly_coefs2\x86\x02\n\x14\x65xoboot_over_network\x12\x39\n\x11send_subject_info\x12\x10.subject_info_eb\x1a\x10.receipt_exoboot\"\x00\x12\'\n\tset_pause\x12\x06.pause\x1a\x10.receipt_exoboot\"\x00\x12%\n\x08set_quit\x12\x05.quit\x1a\x10.receipt_exoboot\"\x00\x12*\n\nset_torque\x12\x08.torques\x1a\x10.receipt_exoboot\"\x00\x12\x37\n\x0fschedule_torque\x12\x10.torque_schedule\x1a\x10.receipt_exoboot\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'exoboot_remote_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_RECEIPT_EXOBOOT']._serialized_start=24
  _globals['_RECEIPT_EXOBOOT']._serialized_end=59
  _globals['_SUBJECT_INFO_EB']._serialized_start=61
  _globals['_SUBJECT_INFO_EB']._serialized_end=138
  _globals['_PAUSE']._serialized_start=140
  _globals['_PAUSE']._serialized_end=163
  _globals['_QUIT']._serialized_start=165
  _globals['_QUIT']._serialized_end=187
  _globals['_TORQUES']._serialized_start=189
  _globals['_TORQUES']._serialized_end=251
  _globals['_POLY_COEFS']._serialized_start=253
  _globals['_POLY_COEFS']._serialized_end=280
  _globals['_TORQUE_SCHEDULE']._serialized_start=282
  _globals['_TORQUE_SCHEDULE']._serialized_end=359
  _globals['_EXOBOOT_OVER_NETWORK']._serialized_start=362
  _globals['_EXOBOOT_OVER_NETWORK']._serialized_end=624
# @@protoc_insertion_point(module_scope)
