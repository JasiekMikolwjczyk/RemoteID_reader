/**
 * @file remote_id_decoder.h
 * @brief ASTM F3411-22 Remote ID Message Decoder for ESP32-S3
 */

#ifndef REMOTE_ID_DECODER_H
#define REMOTE_ID_DECODER_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Transport types
typedef enum {
    RID_TRANSPORT_WIFI = 0,
    RID_TRANSPORT_BLE = 1
} rid_transport_type_t;

// Remote ID Message Types (ASTM F3411-22)
typedef enum {
    RID_MSG_BASIC_ID = 0,
    RID_MSG_LOCATION = 1, 
    RID_MSG_AUTH = 2,
    RID_MSG_SELF_ID = 3,
    RID_MSG_SYSTEM = 4,
    RID_MSG_OPERATOR_ID = 5,
    RID_MSG_MESSAGE_PACK = 15
} rid_message_type_t;

// Message data structure
typedef struct {
    rid_transport_type_t transport;
    uint8_t mac_addr[6];
    int8_t rssi;
    uint32_t timestamp;
    uint16_t payload_len;
    uint8_t payload[];
} __attribute__((packed)) rid_message_data_t;

// Basic ID structure
typedef struct {
    uint8_t id_type;
    uint8_t ua_type; 
    char uas_id[21];
} rid_basic_id_t;

// Location message structure  
typedef struct {
    uint8_t status;
    float latitude;
    float longitude;
    float altitude;
    float speed;
    float direction;
    float vert_speed;
} rid_location_t;

/**
 * @brief Initialize the Remote ID decoder
 */
void rid_decoder_init(void);

/**
 * @brief Parse and decode a Remote ID message pack
 * @param transport Transport type (Wi-Fi or BLE)
 * @param mac_addr MAC address of transmitter
 * @param rssi Signal strength
 * @param pack Message pack data
 * @param pack_len Length of message pack
 * @return Number of messages parsed, -1 on error
 */
int rid_decode_message_pack(rid_transport_type_t transport, const uint8_t *mac_addr,
                           int8_t rssi, const uint8_t *pack, uint16_t pack_len);

/**
 * @brief Output Remote ID frame in structured format
 * @param transport Transport type
 * @param mac_addr MAC address
 * @param rssi Signal strength
 * @param payload Raw payload
 * @param payload_len Payload length
 */
void rid_output_frame(rid_transport_type_t transport, const uint8_t *mac_addr,
                     int8_t rssi, const uint8_t *payload, uint16_t payload_len);

/**
 * @brief Get transport type string
 */
const char* rid_get_transport_string(rid_transport_type_t transport);

/**
 * @brief Format MAC address as string
 */
void rid_format_mac_address(const uint8_t *mac, char *output);

#ifdef __cplusplus
}
#endif

#endif // REMOTE_ID_DECODER_H