import sys
import time
import binascii
import asyncio
import numpy as np
from bleak import discover
from bleak import BleakClient
from bleak.backends.service import BleakGATTServiceCollection

starttime = None
counter = 0

# A Universally Unique Identifier (UUID) is a globally unique 128-bit (16-byte) number 
# that is used to identify profiles, services, and data types in a Generic Attribute (GATT) profile. 
# For efficiency, the Bluetooth® Low Energy (BLE) specification adds support for shortened 16-bit UUIDs
class BLE_device_instance (object):
    BLE_CMD_SERVICE_UUID = "45420100-0000-ffff-ff45-415241424c45"
    BLE_CMD_RX_CHAR_UUID = "45420101-0000-ffff-ff45-415241424c45"
    BLE_CMD_RES_CHAR_UUID = "45420102-0000-ffff-ff45-415241424c45"
    BLE_EER_HDL_CHAR_UUID = "45420103-0000-ffff-ff45-415241424c45"

    BLE_STREAM_SERVICE_UUID = "45420200-0000-ffff-ff45-415241424c45"
    BLE_EEG_STREAM_CHAR_UUID = "45420201-0000-ffff-ff45-415241424c45"
    BLE_IMU_STREAM_CHAR_UUID = "45420202-0000-ffff-ff45-415241424c45"
    BLE_PPG_STREAM_CHAR_UUID = "45420203-0000-ffff-ff45-415241424c45"

    BLE_Commands = {
        'BLE_CMD_GET_FW_VER':binascii.unhexlify("01"),
        'BLE_CMD_GET_BATTERY_LEVEL':binascii.unhexlify("02"),
        'BLE_CMD_DATA_STREAM_CTRL':binascii.unhexlify("03"),
        'BLE_CMD_SOFT_RESET':binascii.unhexlify("05"),
        'BLE_CMD_GET_SERIAL_NUMBER':binascii.unhexlify("06"),
        'BLE_CMD_TIME_SYNC':binascii.unhexlify("07"),
        'BLE_CMD_SET_DEVICE_NAME':binascii.unhexlify("08"),
        'BLE_CMD_GET_DEVICE_NAME':binascii.unhexlify("09"),
        'BLE_CMD_GET_UNIX_TIME':binascii.unhexlify("0B"),
        'BLE_CMD_GET_DEVICE_ID':binascii.unhexlify("0C"),

        'BLE_CMD_GET_FILE_LIST':binascii.unhexlify("10"),
        'BLE_CMD_FILE_TRANSFER_INIT':binascii.unhexlify("11"),
        'BLE_CMD_GET_FILE_DATA':binascii.unhexlify("12"),
        'BLE_CMD_SEG_CRC_CHECK':binascii.unhexlify("13"),
        'BLE_CMD_FILE_CRC_CHECK':binascii.unhexlify("14"),
        'BLE_CMD_FILE_TRANSFER_DEINIT':binascii.unhexlify("15"),

        'BLE_CMD_FDL_INIT':binascii.unhexlify("20"),
        'BLE_CMD_FDL_SEG_CRC':binascii.unhexlify("21"),
        'BLE_CMD_FDL_DATA':binascii.unhexlify("22"),
        'BLE_CMD_FDL_FILE_CRC':binascii.unhexlify("23"),
        'BLE_CMD_FDL_DEINIT':binascii.unhexlify("24"),

        'BLE_CMD_TEST_FORMAT_EXFLASH':binascii.unhexlify("A0"),
        'BLE_CMD_TEST_GET_VOICE_LIST':binascii.unhexlify("A2"),
        'BLE_CMD_TEST_GET_MUSIC_LIST':binascii.unhexlify("AD"),
        'BLE_CMD_TEST_GET_MUSIC_LIST':binascii.unhexlify("A4"),
        'BLE_CMD_TEST_SET_MUSIC_VOLUME':binascii.unhexlify("AF"),
        'BLE_CMD_TEST_START_TEST_SESSION':binascii.unhexlify("A8"),
        'BLE_CMD_TEST_STOP_TEST_SESSION':binascii.unhexlify("A9"),
        'BLE_CMD_TEST_AUDIO_STI_CTRL':binascii.unhexlify("AA"),
        'BLE_CMD_TEST_DATA_COLLECTION_CTRL':binascii.unhexlify("AC"),
        'BLE_CMD_TEST_GET_STI_STATE':binascii.unhexlify("B0"),
        'BLE_CMD_TEST_STOP_AUDIO':binascii.unhexlify("0C"),

        'BLE_CMD_ALARM_GET_SOUND_LIST':binascii.unhexlify("B2"),
        'BLE_CMD_ALARM_SEL_SOUND_TO_PLAY':binascii.unhexlify("B3"),
        'BLE_CMD_ALARM_SET_TIME_WAKEUP':binascii.unhexlify("B4"),
        'BLE_CMD_ALARM_REVIEW_AUDIO':binascii.unhexlify("B5"),
        'BLE_CMD_ALARM_SET_VOLUME':binascii.unhexlify("B6"),

        'BLE_CMD_START_GUIDE_VOICE':binascii.unhexlify("D0"),
        'BLE_CMD_STOP_GUIDE_VOICE':binascii.unhexlify("D1"),

        'BLE_CMD_EN_HW_LOG':binascii.unhexlify("C1"),
        'BLE_CMD_SET_CONTENT_SWITCHING':binascii.unhexlify("C2"),
        'BLE_CMD_CHECK_AUDIO_STATUS':binascii.unhexlify("C3"),
        'BLE_CMD_BACK_TO_SLEEP':binascii.unhexlify("C4"),
        'BLE_CMD_CHECK_AUDIO_CONTENT':binascii.unhexlify("C5"),
        'BLE_CMD_SET_VOICE_SWITCHING':binascii.unhexlify("C6"),

        'BLE_CMD_START_MIC_RECORD':binascii.unhexlify("D3"),
        'BLE_CMD_STOP_MIC_RECORD':binascii.unhexlify("D4"),

        'BLE_CMD_START_NOTIFY_DATA':binascii.unhexlify("E0"),
        'BLE_CMD_SET_AFE_COLLECTION_CHANNEL':binascii.unhexlify("E1"),
        'BLE_CMD_DEEP_SLEEP_STIMULATION':binascii.unhexlify("E2"),
    }

    def __init__ (self):
        self.ble_stream_status = 'start_stream'
        self.raw_eeg_data = []
        self.raw_eeg_pc_timestamps = []
        self.raw_imu_data = []
        self.raw_imu_pc_timestamps = []
        self.raw_ppg_data = []
        self.raw_ppg_pc_timestamps = []

    def hexPrint(self,s):
        s = s.hex()
        new_s = ""
        for i in range(len(s)):
            new_s += s[i]
            if (i + 1) % 2 == 0 and i < (len(s) - 1):
                new_s += ':'
        return new_s

    def ble_cmd_res_notification_handler(self, sender, data):
        if data[:2] == b'\x01\00':
            received_data = self.hexPrint(data)
            print('Firmware version: ', data[2:].decode())
        else:
            received_data = self.hexPrint(data)

        print("BLE COMMAND RESPONSE: ", received_data)
        print('BLE COMMAND RESPONSE LENGTH: ', len(received_data))

    def eeg_notification_handler(self, sender, data):
        global counter, starttime
        #received_data = self.hexPrint(data)
        # print("EEG DATA: ", received_data)
        # print('EEG DATA LENGTH: ', len(data))
        self.raw_eeg_pc_timestamps.append(time.time())
        self.raw_eeg_data.append(np.array(data))
        counter = counter + 9
        if starttime is None:
            starttime = time.time()
        #print('Elapsed time: {}'.format(time.time()-starttime))
        #print('EEG duration: {}'.format(counter/125))
        #print()

    def imu_notification_handler(self, sender, data):
        #received_data = self.hexPrint(data)
        # print("IMU DATA: ", received_data)
        # print('IMU DATA LENGTH: ', len(data))
        self.raw_imu_pc_timestamps.append(time.time())
        self.raw_imu_data.append(np.array(data))

    def ppg_notification_handler(self, sender, data):
        #received_data = self.hexPrint(data)
        # print("PPG DATA: ", received_data)
        # print('PPG DATA LENGTH: ', len(data))
        self.raw_ppg_pc_timestamps.append(time.time())
        self.raw_ppg_data.append(np.array(data))

    def get_data_from_eeg_binary_packet(self, packet_data, n_channels=6):
        is_first_sample = True
        packet_ch_data = [[] for _ in range(n_channels)]
        for sample_i in range (0, 9):
            if is_first_sample:
                is_first_sample = False
                num_channels = int.from_bytes(packet_data[1], byteorder='big', signed=False)
                if num_channels != n_channels:
                    break
                sequence_num = int.from_bytes(packet_data[0], byteorder='big', signed=False)
                timestamp = int.from_bytes(packet_data[2:6], byteorder='big', signed=False)
                packet_ch_data[0].append(int.from_bytes(packet_data[6:9], byteorder='big', signed=True))
                packet_ch_data[1].append(int.from_bytes(packet_data[9:12], byteorder='big', signed=True))
                packet_ch_data[2].append(int.from_bytes(packet_data[12:15], byteorder='big', signed=True))
                packet_ch_data[3].append(int.from_bytes(packet_data[15:18], byteorder='big', signed=True))
                packet_ch_data[4].append(int.from_bytes(packet_data[18:21], byteorder='big', signed=True))
                packet_ch_data[5].append(int.from_bytes(packet_data[21:24], byteorder='big', signed=True))
            else:
                idx = 24 + (19*(sample_i-1))
                packet_ch_data[0].append(int.from_bytes(packet_data[idx+1: idx+4], byteorder='big', signed=True))
                packet_ch_data[1].append(int.from_bytes(packet_data[idx+4: idx+7], byteorder='big', signed=True))
                packet_ch_data[2].append(int.from_bytes(packet_data[idx+7: idx+10], byteorder='big', signed=True))
                packet_ch_data[3].append(int.from_bytes(packet_data[idx+10: idx+13], byteorder='big', signed=True))
                packet_ch_data[4].append(int.from_bytes(packet_data[idx+13: idx+16], byteorder='big', signed=True))
                packet_ch_data[5].append(int.from_bytes(packet_data[idx+16: idx+19], byteorder='big', signed=True))
        return timestamp, sequence_num, np.array(packet_ch_data).T
    
    def get_data_from_imu_binary_packet(self, packet_data, n_channels=3, scaling_factor=9.8/256):
        timestamp_offset = 4
        packet_ch_data = [[] for _ in range(n_channels)]
        timestamp = int.from_bytes(packet_data[0:timestamp_offset], byteorder='big', signed=False)
        for sample_i in range(25):
            packet_ch_data[0].append(int.from_bytes(packet_data[timestamp_offset+(sample_i*6):timestamp_offset+(sample_i*6)+2], \
                                                    byteorder='big', signed=True)*scaling_factor)
            packet_ch_data[1].append(int.from_bytes(packet_data[timestamp_offset+(sample_i*6)+2:timestamp_offset+(sample_i*6)+4], \
                                                    byteorder='big', signed=True)*scaling_factor)
            packet_ch_data[2].append(int.from_bytes(packet_data[timestamp_offset+(sample_i*6)+4:timestamp_offset+(sample_i*6)+6], \
                                                    byteorder='big', signed=True)*scaling_factor)
        return timestamp, np.array(packet_ch_data).T

    # The measured light during green exposure contains most of the information on the pulse wave 
    # (i.e., the heartbeats) and it is typically characterized by a sequence of valleys, 
    # whose time occurrences are used to estimate the heartbeats. 
    # Note that the more the blood is oxygenated, the more the light is absorbed. 
    # Thus, during a heartbeat, there is a high light absorption, 
    # which is observed as a valley in the light output signal.
    # The measured light during the red exposure contains a reference light level 
    # which is used to cancel motion artefacts.

    def get_data_from_ppg_binary_packet(self, packet_data, n_channels=3):
        green = 0x80000
        ir = 0x100000
        red = 0x180000
        timestamp_offset = 4
        iterations = 13 if len(packet_data)==121 else 12
        green_data, ir_data, red_data = [], [], []
        timestamp = int.from_bytes(packet_data[0:timestamp_offset], byteorder='big', signed=False)
        for sample_i in range(iterations):
            for channel_i in range(n_channels):
                byte_data = packet_data[timestamp_offset+(sample_i*9)+(channel_i*3):timestamp_offset+(sample_i*9)+((channel_i*3)+3)]
                binary_data = bin(int.from_bytes(byte_data, byteorder='big', signed=False))
                ch_indicator = binary_data[2:(len(binary_data)-19)]
                if ch_indicator == '1':
                    green_data.append(int.from_bytes(byte_data, byteorder='big', signed=False) ^ green)
                elif ch_indicator == '10':
                    ir_data.append(int.from_bytes(byte_data, byteorder='big', signed=False) ^ ir)
                elif ch_indicator == '11':
                    red_data.append(int.from_bytes(byte_data, byteorder='big', signed=False) ^ red)
        
        # Calculate heart rate from PPG data
        # need to fix this. heart rate can be detected by using extracting the peak of signal 
        # and then calculating the time difference between peaks
        heart_rate = len(green_data) / (timestamp / 1000) * 60
        
        return timestamp, np.array([green_data, ir_data, red_data]).T, heart_rate
    
    def close(self):
        # Stop BLE data streaming
        #params = b'\xFF\x00'
        #await self.client.write_gatt_char(self.BLE_CMD_RX_CHAR_UUID,  self.BLE_Commands['BLE_CMD_DATA_STREAM_CTRL'] + params, True)
        print('CLOSING')
        self.ble_stream_status = 'stop_stream'

    async def main(self, address):
        params = b''
        async with BleakClient(address) as client:
            print(f"Connected: {client.is_connected}")
            self.client = client

            # Register all notification characteristics
            await client.start_notify(self.BLE_CMD_RES_CHAR_UUID, self.ble_cmd_res_notification_handler)
            await client.start_notify(self.BLE_EEG_STREAM_CHAR_UUID, self.eeg_notification_handler)
            await client.start_notify(self.BLE_IMU_STREAM_CHAR_UUID, self.imu_notification_handler)
            await client.start_notify(self.BLE_PPG_STREAM_CHAR_UUID, self.ppg_notification_handler)
            
            # Get firmware verson
            await client.write_gatt_char(self.BLE_CMD_RX_CHAR_UUID,  self.BLE_Commands['BLE_CMD_GET_FW_VER'], False)

            # Send time sync command
            unix_time = int(time.time()).to_bytes(4, byteorder='big')
            await client.write_gatt_char(self.BLE_CMD_RX_CHAR_UUID,  self.BLE_Commands['BLE_CMD_TIME_SYNC'] + unix_time, False)
            
            # Start BLE data streaming
            #params = b'\xFF\x01'
            #await client.write_gatt_char(self.BLE_CMD_RX_CHAR_UUID,  self.BLE_Commands['BLE_CMD_DATA_STREAM_CTRL'] + params, True)
                    
            # Stop BLE data streaming
            #params = b'\xFF\x00'
            #await client.write_gatt_char(self.BLE_CMD_RX_CHAR_UUID,  self.BLE_Commands['BLE_CMD_DATA_STREAM_CTRL'] + params, True)
                        
            while True:
                if self.ble_stream_status == 'start_stream':
                    self.ble_stream_status = 'idle'
                    print('Start BLE Streaming')
                    # Temporarily stop BLE data streaming at the beginning
                    params = b'\xFF\x00'
                    await client.write_gatt_char(self.BLE_CMD_RX_CHAR_UUID,  self.BLE_Commands['BLE_CMD_DATA_STREAM_CTRL'] + params, False)
                    await asyncio.sleep(1)
                    # Start BLE data streaming
                    params = b'\xFF\x01'
                    await client.write_gatt_char(self.BLE_CMD_RX_CHAR_UUID,  self.BLE_Commands['BLE_CMD_DATA_STREAM_CTRL'] + params, False)
                elif self.ble_stream_status == 'stop_stream':
                    self.ble_stream_status = 'idle'
                    print('Stop BLE Streaming')
                    # Temporarily stop BLE data streaming at the beginning
                    params = b'\xFF\x00'
                    await client.write_gatt_char(self.BLE_CMD_RX_CHAR_UUID,  self.BLE_Commands['BLE_CMD_DATA_STREAM_CTRL'] + params, False)

                    await asyncio.sleep(1)
                    print('Client closed')
                else:
                    pass
                
                await asyncio.sleep(0.05)
            