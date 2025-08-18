/**
 * @file main.c
 * @brief ESP32-S3 Remote ID Sniffer - Automatic Wi-Fi NAN & BLE Scanner
 * 
 * This firmware automatically starts scanning for Remote ID broadcasts
 * on both Wi-Fi NAN and BLE protocols upon power-up.
 */

#include <stdio.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "driver/gpio.h"

// Wi-Fi includes
#include "esp_wifi.h"
#include "esp_private/wifi.h"

// BLE includes
#include "esp_bt.h"
#include "esp_gap_ble_api.h"
#include "esp_bt_main.h"
#include "esp_bt_device.h"

#include "remote_id_decoder.h"

// Tags for logging
#define TAG_MAIN "RID_MAIN"
#define TAG_WIFI "RID_WIFI"
#define TAG_BLE  "RID_BLE"

// GPIO Pin definitions for status signals (based on schematic)
#define REMID_RDY_PIN    GPIO_NUM_42   // READY signal to mPCIe pin 42
#define REMID_WARN_PIN   GPIO_NUM_44   // WARNING signal to mPCIe pin 44  
#define REMID_MSG_PIN    GPIO_NUM_46   // MESSAGE signal to mPCIe pin 46
#define STATUS_LED_PIN   GPIO_NUM_2    // Built-in LED or external LED

// Wi-Fi Configuration
#define WIFI_CHANNEL 6
#define MAX_PACKET_SIZE 512

// BLE Configuration
#define SCAN_DURATION 0  // Continuous scan
#define SCAN_INTERVAL 0x50
#define SCAN_WINDOW 0x30


// Remote ID identifiers
static const uint8_t ASTM_REMOTE_ID_WIFI_OUI[] = {0xFA, 0x0B, 0xBC};
static const uint16_t ASTM_REMOTE_ID_BLE_UUID = 0xFFFA;

// Task handles
static TaskHandle_t wifi_task_handle = NULL;
static TaskHandle_t ble_task_handle = NULL;

// Statistics
static uint32_t wifi_packets_received = 0;
static uint32_t ble_advs_received = 0;
static uint32_t remote_id_frames_found = 0;

// LED control variables
static bool led_state = false;
static uint32_t last_frame_time = 0;
static bool detection_mode = false;

/**
 * @brief Initialize status pins and LED - ALL set to LOW
 */
static esp_err_t init_gpio_pins(void)
{
    ESP_LOGI(TAG_MAIN, "Initializing GPIO pins...");
    
    // Configure status pins as outputs (always LOW)
    gpio_config_t status_conf = {
        .pin_bit_mask = (1ULL << REMID_RDY_PIN) | 
                       (1ULL << REMID_WARN_PIN) | 
                       (1ULL << REMID_MSG_PIN),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&status_conf));
    
    // Configure LED pin as output
    gpio_config_t led_conf = {
        .pin_bit_mask = (1ULL << STATUS_LED_PIN),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&led_conf));
    
    // Set ALL pins to LOW (0V) - status pins stay LOW always
    gpio_set_level(REMID_RDY_PIN, 0);
    gpio_set_level(REMID_WARN_PIN, 0);
    gpio_set_level(REMID_MSG_PIN, 0);
    gpio_set_level(STATUS_LED_PIN, 0);
    
    ESP_LOGI(TAG_MAIN, "All pins set to LOW - Status pins stay LOW always");
    
    return ESP_OK;
}

/**
 * @brief LED control task - blinks LED to show system status
 */
static void led_control_task(void *pvParameters)
{
    const uint32_t normal_blink_period = 1000;  // 1 second (1Hz) when active
    const uint32_t fast_blink_period = 200;     // 200ms (5Hz) when detecting frames
    const uint32_t fast_mode_duration = 3000;   // Stay in fast mode for 3 seconds after last frame
    
    while (1) {
        uint32_t current_time = xTaskGetTickCount() * portTICK_PERIOD_MS;
        uint32_t time_since_last_frame = current_time - last_frame_time;
        
        // Determine blink rate based on recent frame detection
        uint32_t blink_period;
        if (time_since_last_frame < fast_mode_duration) {
            blink_period = fast_blink_period;  // Fast blink - frames detected recently
            detection_mode = true;
        } else {
            blink_period = normal_blink_period; // Slow blink - normal operation
            detection_mode = false;
        }
        
        // Toggle LED
        led_state = !led_state;
        gpio_set_level(STATUS_LED_PIN, led_state ? 1 : 0);
        
        // Wait for next blink
        vTaskDelay(blink_period / portTICK_PERIOD_MS);
    }
}

/**
 * @brief Wi-Fi packet callback for promiscuous mode
 */
static void wifi_promiscuous_cb(void *buf, wifi_promiscuous_pkt_type_t type)
{
    if (type != WIFI_PKT_MGMT) return;
    
    wifi_promiscuous_pkt_t *pkt = (wifi_promiscuous_pkt_t *)buf;
    const uint8_t *payload = pkt->payload;
    uint32_t len = pkt->rx_ctrl.sig_len;
    
    wifi_packets_received++;
    
    // Look for Remote ID in management frames
    if (len > 24) {
        // Check for Remote ID OUI in vendor specific elements
        for (int i = 0; i < len - 3; i++) {
            if (memcmp(&payload[i], ASTM_REMOTE_ID_WIFI_OUI, 3) == 0) {
                // Found potential Remote ID frame
                ESP_LOGI(TAG_WIFI, "Potential Remote ID Wi-Fi frame detected");
                
                // Extract MAC address from frame header
                uint8_t mac_addr[6];
                memcpy(mac_addr, &payload[10], 6); // Source MAC
                
                // Extract Remote ID payload (after OUI)
                const uint8_t *rid_payload = &payload[i + 3];
                uint16_t rid_len = len - i - 3;
                
                if (rid_len >= 25) {
                    remote_id_frames_found++;
                    
                    // Update last frame time for LED fast blink mode
                    last_frame_time = xTaskGetTickCount() * portTICK_PERIOD_MS;
                    
                    rid_output_frame(RID_TRANSPORT_WIFI, mac_addr, 
                                   pkt->rx_ctrl.rssi, rid_payload, rid_len);
                }
                break;
            }
        }
    }
}

/**
 * @brief Initialize Wi-Fi in promiscuous mode
 */
static esp_err_t init_wifi(void)
{
    ESP_LOGI(TAG_WIFI, "Initializing Wi-Fi scanner...");
    
    esp_netif_init();
    esp_event_loop_create_default();
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_NULL));
    ESP_ERROR_CHECK(esp_wifi_start());
    
    // Enable promiscuous mode
    ESP_ERROR_CHECK(esp_wifi_set_promiscuous(true));
    ESP_ERROR_CHECK(esp_wifi_set_promiscuous_rx_cb(&wifi_promiscuous_cb));
    
    // Set channel
    ESP_ERROR_CHECK(esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE));
    
    ESP_LOGI(TAG_WIFI, "Wi-Fi scanner started on channel %d", WIFI_CHANNEL);
    return ESP_OK;
}

/**
 * @brief BLE scan result callback
 */
static void ble_scan_result_cb(esp_gap_ble_cb_event_t event, esp_ble_gap_cb_param_t *param)
{
    switch (event) {
    case ESP_GAP_BLE_SCAN_RESULT_EVT: {
        esp_ble_gap_cb_param_t *scan_result = (esp_ble_gap_cb_param_t *)param;
        
        if (scan_result->scan_rst.search_evt == ESP_GAP_SEARCH_INQ_RES_EVT) {
            ble_advs_received++;
            
            uint8_t *adv_data = scan_result->scan_rst.ble_adv;
            uint8_t adv_len = scan_result->scan_rst.adv_data_len;
            
            // Look for Remote ID service UUID (0xFFFA)
            for (int i = 0; i < adv_len - 3; i++) {
                // Check for 16-bit service UUID AD type (0x03 or 0x02)
                if ((adv_data[i] == 0x03 && adv_data[i+1] == 0x03) || 
                    (adv_data[i] == 0x05 && adv_data[i+1] == 0x02)) {
                    
                    uint16_t uuid = (adv_data[i+3] << 8) | adv_data[i+2];
                    
                    if (uuid == ASTM_REMOTE_ID_BLE_UUID) {
                        ESP_LOGI(TAG_BLE, "Remote ID BLE advertisement found");
                        
                        // Look for service data with Remote ID payload
                        for (int j = i + 4; j < adv_len - 25; j++) {
                            if (adv_data[j] == 0x16 && adv_data[j+1] >= 25) { // Service data
                                uint16_t service_uuid = (adv_data[j+3] << 8) | adv_data[j+2];
                                if (service_uuid == ASTM_REMOTE_ID_BLE_UUID) {
                                    // Found Remote ID service data
                                    const uint8_t *rid_payload = &adv_data[j+4];
                                    uint8_t rid_len = adv_data[j+1] - 2; // Minus UUID
                                    
                                    if (rid_len >= 25) {
                                        remote_id_frames_found++;
                                        
                                        // Update last frame time for LED fast blink mode
                                        last_frame_time = xTaskGetTickCount() * portTICK_PERIOD_MS;
                                        
                                        rid_output_frame(RID_TRANSPORT_BLE, 
                                                       scan_result->scan_rst.bda,
                                                       scan_result->scan_rst.rssi,
                                                       rid_payload, rid_len);
                                    }
                                    goto next_advertisement;
                                }
                            }
                        }
                        break;
                    }
                }
            }
            next_advertisement:;
        }
        break;
    }
    case ESP_GAP_BLE_SCAN_START_COMPLETE_EVT:
        if (param->scan_start_cmpl.status == ESP_BT_STATUS_SUCCESS) {
            ESP_LOGI(TAG_BLE, "BLE scan started successfully");
        }
        break;
    case ESP_GAP_BLE_SCAN_STOP_COMPLETE_EVT:
        ESP_LOGI(TAG_BLE, "BLE scan stopped");
        break;
    default:
        break;
    }
}

/**
 * @brief Initialize BLE scanner
 */
static esp_err_t init_ble(void)
{
    ESP_LOGI(TAG_BLE, "Initializing BLE scanner...");
    
    esp_bt_controller_config_t bt_cfg = BT_CONTROLLER_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_bt_controller_init(&bt_cfg));
    ESP_ERROR_CHECK(esp_bt_controller_enable(ESP_BT_MODE_BLE));
    
    ESP_ERROR_CHECK(esp_bluedroid_init());
    ESP_ERROR_CHECK(esp_bluedroid_enable());
    
    // Register callback
    ESP_ERROR_CHECK(esp_ble_gap_register_callback(ble_scan_result_cb));
    
    // Configure scan parameters
    static esp_ble_scan_params_t scan_params = {
        .scan_type = BLE_SCAN_TYPE_ACTIVE,
        .own_addr_type = BLE_ADDR_TYPE_PUBLIC,
        .scan_filter_policy = BLE_SCAN_FILTER_ALLOW_ALL,
        .scan_interval = SCAN_INTERVAL,
        .scan_window = SCAN_WINDOW,
        .scan_duplicate = BLE_SCAN_DUPLICATE_DISABLE
    };
    
    ESP_ERROR_CHECK(esp_ble_gap_set_scan_params(&scan_params));
    ESP_ERROR_CHECK(esp_ble_gap_start_scanning(SCAN_DURATION));
    
    ESP_LOGI(TAG_BLE, "BLE scanner started");
    return ESP_OK;
}

/**
 * @brief Statistics task - print periodic statistics
 */
static void stats_task(void *pvParameters)
{
    while (1) {
        vTaskDelay(30000 / portTICK_PERIOD_MS); // Every 30 seconds
        
        ESP_LOGI(TAG_MAIN, "=== STATISTICS ===");
        ESP_LOGI(TAG_MAIN, "Wi-Fi packets: %lu", wifi_packets_received);
        ESP_LOGI(TAG_MAIN, "BLE advertisements: %lu", ble_advs_received);
        ESP_LOGI(TAG_MAIN, "Remote ID frames: %lu", remote_id_frames_found);
        ESP_LOGI(TAG_MAIN, "================");
    }
}

/**
 * @brief Main application entry point
 */
void app_main(void)
{
    printf("\n");
    printf("=================================================\n");
    printf("🚁 ESP32-S3 Remote ID Sniffer v1.0\n");
    printf("   Automatic Wi-Fi NAN & BLE Scanner\n");
    printf("=================================================\n\n");
    
    ESP_LOGI(TAG_MAIN, "ESP32-S3 Remote ID Sniffer starting...");
    
    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    
    // Initialize GPIO pins (all set to LOW)
    ESP_ERROR_CHECK(init_gpio_pins());
    
    // Initialize Remote ID decoder
    rid_decoder_init();
    
    // Initialize Wi-Fi scanner
    ESP_ERROR_CHECK(init_wifi());
    
    // Initialize BLE scanner  
    ESP_ERROR_CHECK(init_ble());
    
    // Start LED control task
    xTaskCreate(led_control_task, "led_task", 2048, NULL, 2, NULL);
    
    // Start statistics task
    xTaskCreate(stats_task, "stats_task", 2048, NULL, 1, NULL);
    
    printf("\n🎯 Remote ID Sniffer is now active!\n");
    printf("📡 Scanning Wi-Fi channel %d and BLE advertisements\n", WIFI_CHANNEL);
    printf("📊 Connect via USB serial at 115200 baud to see detected frames\n");
    printf("💡 LED: Slow blink = Active, Fast blink = Detecting frames\n\n");
    
    ESP_LOGI(TAG_MAIN, "System ready - all status pins LOW, LED active");
    
    // Main loop - keep alive
    while (1) {
        vTaskDelay(1000 / portTICK_PERIOD_MS);
    }
}