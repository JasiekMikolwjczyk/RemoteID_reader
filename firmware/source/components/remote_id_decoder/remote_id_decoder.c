/**
 * @file remote_id_decoder.c  
 * @brief Simple Remote ID Frame Output - NO DECODING, RAW ONLY
 */

#include <stdio.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include "esp_log.h"
#include "remote_id_decoder.h"

#define TAG "RID_OUTPUT"

// Frame counter for structured output
static uint32_t frame_counter = 0;

void rid_decoder_init(void)
{
    ESP_LOGI(TAG, "Remote ID Raw Output initialized - NO DECODING");
    frame_counter = 0;
}

const char* rid_get_transport_string(rid_transport_type_t transport)
{
    switch(transport) {
        case RID_TRANSPORT_WIFI: return "WIFI";
        case RID_TRANSPORT_BLE: return "BLE"; 
        default: return "UNKNOWN";
    }
}

void rid_format_mac_address(const uint8_t *mac, char *output)
{
    sprintf(output, "%02X:%02X:%02X:%02X:%02X:%02X",
            mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

static uint32_t get_timestamp_ms(void)
{
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (tv.tv_sec * 1000) + (tv.tv_usec / 1000);
}

void rid_output_frame(rid_transport_type_t transport, const uint8_t *mac_addr,
                     int8_t rssi, const uint8_t *payload, uint16_t payload_len)
{
    char mac_str[18];
    rid_format_mac_address(mac_addr, mac_str);
    
    frame_counter++;
    uint32_t timestamp = get_timestamp_ms();
    
    // Output ONLY structured frame data for computer processing
    printf("RID_FRAME_START\n");
    printf("TIMESTAMP=%lu\n", timestamp);
    printf("TRANSPORT=%s\n", rid_get_transport_string(transport));
    printf("MAC=%s\n", mac_str);
    printf("RSSI=%d\n", rssi);
    printf("LENGTH=%d\n", payload_len);
    printf("PAYLOAD=");
    
    // Output payload as hex string
    for (int i = 0; i < payload_len; i++) {
        printf("%02X", payload[i]);
    }
    printf("\n");
    printf("RID_FRAME_END\n");
}

// Dummy functions to satisfy header - NOT USED
int rid_decode_message_pack(rid_transport_type_t transport, const uint8_t *mac_addr,
                           int8_t rssi, const uint8_t *pack, uint16_t pack_len)
{
    return 0; // Not implemented - decoding on computer
}