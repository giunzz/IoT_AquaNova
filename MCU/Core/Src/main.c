/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include "DS18B20.h"
#include "CLCD_I2C.h"
#include "feeding.h"
#include "DS3231.h"
#include "lcd_state.h"
#include "string.h"

void read_sensors_data(void);
void process_turbidity(void);
void measure_food_level(void);
void handle_turbidity_warning(void);
void handle_uart_transmission(void);

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc1;

I2C_HandleTypeDef hi2c1;
I2C_HandleTypeDef hi2c2;

TIM_HandleTypeDef htim1;
TIM_HandleTypeDef htim2;
TIM_HandleTypeDef htim4;

UART_HandleTypeDef huart1;

/* USER CODE BEGIN PV */
DS18B20_Name DS1;
float TEMP;
CLCD_I2C_Name LCD1;
uint32_t adcValue;
float voltage, turbidity;
DS3231_Time_t timenow;
char lcd_info_buffer[20];

LCD_State_t lcd_state = LCD_STATE_NORMAL;

uint32_t pMillis;		// 4 dong nay de khai bao ultrasonic
uint32_t Value1 = 0;
uint32_t Value2 = 0;
float Distance = 0.0f; // cm

float D_empty = 10.0f;   // cm
float D_full  = 5.0f;   // cm
float percent;

uint8_t is_turbidity_warning_active = 0;      
uint8_t is_warning_silenced_by_user = 0;   
uint32_t last_beep_toggle_time = 0;

char rec;
char buffer[100];
int i=0;

char uart_tx_buffer[100]; 
uint32_t last_uart_send_time = 0; 
//#define UART_SEND_INTERVAL 3600000 
#define UART_SEND_INTERVAL 60000 

//uint32_t lcd_timer = 0;

//uint32_t lcd_command_timer = 0; 
//char lcd_command_buffer[20];  

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
  if (huart->Instance == USART1) 
  {
    switch (rec)
    {
      case 'L':
				HAL_GPIO_WritePin(LIGHT_GPIO_Port, LIGHT_Pin, GPIO_PIN_SET);
				lcd_state = LCD_STATE_LIGHT_ON; 
				lcd_timer = HAL_GetTick(); 
        break;

      case 'l':
				HAL_GPIO_WritePin(LIGHT_GPIO_Port, LIGHT_Pin, GPIO_PIN_RESET);
				lcd_state = LCD_STATE_LIGHT_OFF; 
				lcd_timer = HAL_GetTick(); 
        break;
				
      case 'F':
				feeding_Alarm();
        break;
			
      default:
        break;			
    }

    HAL_UART_Receive_IT(&huart1, (uint8_t *)&rec, 1);
  }
}

uint16_t Read_ADC(void) 														// Doc ADC
{
    uint16_t val = 0;
    HAL_ADC_Start(&hadc1);                              
    if (HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK) 
    {
        val = HAL_ADC_GetValue(&hadc1);                
    }
    HAL_ADC_Stop(&hadc1);
    return val;
}

uint32_t Read_ADC_Avg(uint8_t samples)			// Doc ADC lay nhieu mau
{
    uint32_t sum = 0;
    for(uint8_t i = 0; i < samples; i++)
    {
        HAL_ADC_Start(&hadc1);
        HAL_ADC_PollForConversion(&hadc1, 10);
        sum += HAL_ADC_GetValue(&hadc1);
        HAL_ADC_Stop(&hadc1);
    }
    return sum / samples;
}


struct feeding_t feed = {
		.hi2c = &hi2c1,
		.htim = &htim4,
		.channel = TIM_CHANNEL_4,
		.alarm_time = {
				.seconds = 0,
				.minutes = 00,
				.hour = 15,
		},
};

void LCD_Update(void) {
    char buffer[20];
	
    if (is_turbidity_warning_active == 1)
    {
        CLCD_I2C_SetCursor(&LCD1, 0, 0);
        CLCD_I2C_WriteString(&LCD1, "  !!WARNING!!   ");
        CLCD_I2C_SetCursor(&LCD1, 0, 1);
        CLCD_I2C_WriteString(&LCD1, " TURBIDITY HIGH ");
        return;
    }

    switch(lcd_state) {
        case LCD_STATE_FEEDING:
            //CLCD_I2C_Clear(&LCD1);
            CLCD_I2C_SetCursor(&LCD1, 0, 0);
            CLCD_I2C_WriteString(&LCD1, "  FEEDING ...   ");
            CLCD_I2C_SetCursor(&LCD1, 0, 1);
            CLCD_I2C_WriteString(&LCD1, "                ");
				
            if (HAL_GetTick() - lcd_timer >= 1000) {
                lcd_state = LCD_STATE_NORMAL;
                CLCD_I2C_Clear(&LCD1);
            }
            break;

        case LCD_STATE_TIMESET:
            //CLCD_I2C_Clear(&LCD1);
            sprintf(buffer, "Set: %02d:%02d:%02d         ",
                    feed.alarm_time.hour,
                    feed.alarm_time.minutes,
                    feed.alarm_time.seconds);
            CLCD_I2C_SetCursor(&LCD1, 0, 0);
            CLCD_I2C_WriteString(&LCD1, buffer);
				    CLCD_I2C_SetCursor(&LCD1, 0, 1);
            CLCD_I2C_WriteString(&LCD1, "                ");
				
						if (HAL_GetTick() - lcd_timer >= 2000) {
                lcd_state = LCD_STATE_NORMAL;
                CLCD_I2C_Clear(&LCD1);
            }
            break;
						
        case LCD_STATE_INFO:
						sprintf(buffer, "Time: %02d:%02d:%02d    ", 
            timenow.hour, timenow.minutes, timenow.seconds);
						CLCD_I2C_SetCursor(&LCD1, 0, 0);
						CLCD_I2C_WriteString(&LCD1, buffer);

						if (feed.IsAlarmEnabled == 1) {
							sprintf(buffer, "Alarm: %02d:00:00     ", feed.alarm_time.hour);
						} else {
								sprintf(buffer, "No set alarm    ");
						}
						CLCD_I2C_SetCursor(&LCD1, 0, 1);
						CLCD_I2C_WriteString(&LCD1, buffer);
						
            if (HAL_GetTick() - lcd_timer >= 2000) { 
                lcd_state = LCD_STATE_NORMAL;
                CLCD_I2C_Clear(&LCD1);
            }
            break;						

        case LCD_STATE_SET:
            CLCD_I2C_SetCursor(&LCD1, 0, 0);
            CLCD_I2C_WriteString(&LCD1, "Time's been set "); 
            CLCD_I2C_SetCursor(&LCD1, 0, 1);
            CLCD_I2C_WriteString(&LCD1, "                ");

            if (HAL_GetTick() - lcd_timer >= 2000) { 
                lcd_state = LCD_STATE_NORMAL;
                CLCD_I2C_Clear(&LCD1);
            }
            break;	

        case LCD_STATE_SET_OFF:
            CLCD_I2C_SetCursor(&LCD1, 0, 0);
            CLCD_I2C_WriteString(&LCD1, "Alarm's deleted ");
				    CLCD_I2C_SetCursor(&LCD1, 0, 1);
            CLCD_I2C_WriteString(&LCD1, "                ");
				
						if (HAL_GetTick() - lcd_timer >= 2000) {
                lcd_state = LCD_STATE_NORMAL;
                CLCD_I2C_Clear(&LCD1);
            }
            break;

        case LCD_STATE_LIGHT_ON:
            CLCD_I2C_SetCursor(&LCD1, 0, 0);
            CLCD_I2C_WriteString(&LCD1, "  Light was on  ");
				    CLCD_I2C_SetCursor(&LCD1, 0, 1);
            CLCD_I2C_WriteString(&LCD1, "                ");
				
						if (HAL_GetTick() - lcd_timer >= 1000) {
                lcd_state = LCD_STATE_NORMAL;
                CLCD_I2C_Clear(&LCD1);
            }
            break;
						
        case LCD_STATE_LIGHT_OFF:
            CLCD_I2C_SetCursor(&LCD1, 0, 0);
            CLCD_I2C_WriteString(&LCD1, "  Light was off ");
				    CLCD_I2C_SetCursor(&LCD1, 0, 1);
            CLCD_I2C_WriteString(&LCD1, "                ");
				
						if (HAL_GetTick() - lcd_timer >= 1000) {
                lcd_state = LCD_STATE_NORMAL;
                CLCD_I2C_Clear(&LCD1);
            }
            break;
						
				case LCD_STATE_DISTANCE:
						sprintf(buffer, "Dist: %.1f cm   ", Distance);
						CLCD_I2C_SetCursor(&LCD1, 0, 0);
						CLCD_I2C_WriteString(&LCD1, buffer);

						sprintf(buffer, "Feed: %.0f%%      ", percent);
						CLCD_I2C_SetCursor(&LCD1, 0, 1);
						CLCD_I2C_WriteString(&LCD1, buffer);

						if (HAL_GetTick() - lcd_timer >= 10000) {
						lcd_state = LCD_STATE_NORMAL;
						CLCD_I2C_Clear(&LCD1);
						}
						break;	
						
        case LCD_STATE_NORMAL:
        default:
            sprintf(buffer,"Temp: %.1f C       ", TEMP);
            CLCD_I2C_SetCursor(&LCD1, 0, 0);
            CLCD_I2C_WriteString(&LCD1, buffer);

            sprintf(buffer,"Turb: %.1f NTU      ", turbidity);
            CLCD_I2C_SetCursor(&LCD1, 0, 1);
            CLCD_I2C_WriteString(&LCD1, buffer);
            break;
				
    }
}

void HCSR04_Read(void)
{
  HAL_GPIO_WritePin(TRIG_HCSR04_GPIO_Port, TRIG_HCSR04_Pin, GPIO_PIN_SET);
  __HAL_TIM_SET_COUNTER(&htim2, 0);
  while (__HAL_TIM_GET_COUNTER(&htim2) < 10); // 10us pulse
  HAL_GPIO_WritePin(TRIG_HCSR04_GPIO_Port, TRIG_HCSR04_Pin, GPIO_PIN_RESET);

  pMillis = HAL_GetTick();
  while (!(HAL_GPIO_ReadPin(ECHO_GPIO_Port, ECHO_Pin)) && (HAL_GetTick() - pMillis) < 20);
  Value1 = __HAL_TIM_GET_COUNTER(&htim2);

  pMillis = HAL_GetTick();
  while ((HAL_GPIO_ReadPin(ECHO_GPIO_Port, ECHO_Pin)) && (HAL_GetTick() - pMillis) < 50);
  Value2 = __HAL_TIM_GET_COUNTER(&htim2);

  Distance = (float)(Value2 - Value1) * 0.034 / 2;
}

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_I2C2_Init(void);
static void MX_TIM1_Init(void);
static void MX_ADC1_Init(void);
static void MX_I2C1_Init(void);
static void MX_TIM4_Init(void);
static void MX_TIM2_Init(void);
static void MX_USART1_UART_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
    if (GPIO_Pin == BUTTON_CONTROL_Pin || GPIO_Pin == BUTTON_UP_Pin || 
        GPIO_Pin == BUTTON_DOWN_Pin || GPIO_Pin == BUTTON_Pin)
    {
				if (is_turbidity_warning_active)
        {
            is_turbidity_warning_active = 0;   
            is_warning_silenced_by_user = 1;  
            HAL_GPIO_WritePin(BUZZER_GPIO_Port, BUZZER_Pin, GPIO_PIN_RESET); 
            lcd_state = LCD_STATE_NORMAL;
            
            return; 
        }
    }
	
    feeding_ISR(GPIO_Pin);
}

void HAL_SYSTICK_Callback(void)
{
		// dong co quay trong 1s
		static uint32_t counter = 0;
    if(counter >= 1000) {  
    	feed.IsFeed = 3;
        counter = 0;
    }
    if (feed.IsFeed == 2) {
        counter++;
    }
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_I2C2_Init();
  MX_TIM1_Init();
  MX_ADC1_Init();
  MX_I2C1_Init();
  MX_TIM4_Init();
  MX_TIM2_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
	CLCD_I2C_Init(&LCD1,&hi2c2, 0x4e, 16, 2);
	DS18B20_Init(&DS1, &htim1, DS18B20_GPIO_Port, DS18B20_Pin);
	feeding_Init(&feed);
	
	HAL_TIM_Base_Start(&htim2);  // dung cho ultra sonic
  HAL_GPIO_WritePin(TRIG_HCSR04_GPIO_Port, TRIG_HCSR04_Pin, GPIO_PIN_RESET);

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
		feeding_Handler();          
    read_sensors_data();        
    process_turbidity();        
    measure_food_level();      
    handle_turbidity_warning(); 
    LCD_Update();               
    handle_uart_transmission(); 
    		
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_ADC;
  PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV6;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief ADC1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC1_Init(void)
{

  /* USER CODE BEGIN ADC1_Init 0 */

  /* USER CODE END ADC1_Init 0 */

  ADC_ChannelConfTypeDef sConfig = {0};

  /* USER CODE BEGIN ADC1_Init 1 */

  /* USER CODE END ADC1_Init 1 */

  /** Common config
  */
  hadc1.Instance = ADC1;
  hadc1.Init.ScanConvMode = ADC_SCAN_DISABLE;
  hadc1.Init.ContinuousConvMode = DISABLE;
  hadc1.Init.DiscontinuousConvMode = DISABLE;
  hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc1.Init.NbrOfConversion = 1;
  if (HAL_ADC_Init(&hadc1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure Regular Channel
  */
  sConfig.Channel = ADC_CHANNEL_1;
  sConfig.Rank = ADC_REGULAR_RANK_1;
  sConfig.SamplingTime = ADC_SAMPLETIME_1CYCLE_5;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN ADC1_Init 2 */

  /* USER CODE END ADC1_Init 2 */

}

/**
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C1_Init(void)
{

  /* USER CODE BEGIN I2C1_Init 0 */

  /* USER CODE END I2C1_Init 0 */

  /* USER CODE BEGIN I2C1_Init 1 */

  /* USER CODE END I2C1_Init 1 */
  hi2c1.Instance = I2C1;
  hi2c1.Init.ClockSpeed = 100000;
  hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c1.Init.OwnAddress1 = 0;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2 = 0;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C1_Init 2 */

  /* USER CODE END I2C1_Init 2 */

}

/**
  * @brief I2C2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C2_Init(void)
{

  /* USER CODE BEGIN I2C2_Init 0 */

  /* USER CODE END I2C2_Init 0 */

  /* USER CODE BEGIN I2C2_Init 1 */

  /* USER CODE END I2C2_Init 1 */
  hi2c2.Instance = I2C2;
  hi2c2.Init.ClockSpeed = 100000;
  hi2c2.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c2.Init.OwnAddress1 = 0;
  hi2c2.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c2.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c2.Init.OwnAddress2 = 0;
  hi2c2.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c2.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C2_Init 2 */

  /* USER CODE END I2C2_Init 2 */

}

/**
  * @brief TIM1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM1_Init(void)
{

  /* USER CODE BEGIN TIM1_Init 0 */

  /* USER CODE END TIM1_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM1_Init 1 */

  /* USER CODE END TIM1_Init 1 */
  htim1.Instance = TIM1;
  htim1.Init.Prescaler = 72-1;
  htim1.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim1.Init.Period = 0xffff-1;
  htim1.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim1.Init.RepetitionCounter = 0;
  htim1.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim1) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim1, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim1, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM1_Init 2 */

  /* USER CODE END TIM1_Init 2 */

}

/**
  * @brief TIM2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM2_Init(void)
{

  /* USER CODE BEGIN TIM2_Init 0 */

  /* USER CODE END TIM2_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};

  /* USER CODE BEGIN TIM2_Init 1 */

  /* USER CODE END TIM2_Init 1 */
  htim2.Instance = TIM2;
  htim2.Init.Prescaler = 71;
  htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim2.Init.Period = 65535;
  htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim2) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim2, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim2, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM2_Init 2 */

  /* USER CODE END TIM2_Init 2 */

}

/**
  * @brief TIM4 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM4_Init(void)
{

  /* USER CODE BEGIN TIM4_Init 0 */

  /* USER CODE END TIM4_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM4_Init 1 */

  /* USER CODE END TIM4_Init 1 */
  htim4.Instance = TIM4;
  htim4.Init.Prescaler = 144-1;
  htim4.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim4.Init.Period = 10000-1;
  htim4.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;
  if (HAL_TIM_Base_Init(&htim4) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim4, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim4) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim4, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_4) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM4_Init 2 */

  /* USER CODE END TIM4_Init 2 */
  HAL_TIM_MspPostInit(&htim4);

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 9600;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOA, TRIG_HCSR04_Pin|BUZZER_Pin|LIGHT_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(DS18B20_GPIO_Port, DS18B20_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin : LED_Pin */
  GPIO_InitStruct.Pin = LED_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LED_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : ECHO_Pin */
  GPIO_InitStruct.Pin = ECHO_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(ECHO_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : TRIG_HCSR04_Pin BUZZER_Pin LIGHT_Pin */
  GPIO_InitStruct.Pin = TRIG_HCSR04_Pin|BUZZER_Pin|LIGHT_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  /*Configure GPIO pins : ALARM_Pin BUTTON_CONTROL_Pin BUTTON_Pin */
  GPIO_InitStruct.Pin = ALARM_Pin|BUTTON_CONTROL_Pin|BUTTON_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_FALLING;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /*Configure GPIO pin : DS18B20_Pin */
  GPIO_InitStruct.Pin = DS18B20_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(DS18B20_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pin : BUTTON_OFF_Pin */
  GPIO_InitStruct.Pin = BUTTON_OFF_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_FALLING;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(BUTTON_OFF_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : BUTTON_DOWN_Pin BUTTON_UP_Pin */
  GPIO_InitStruct.Pin = BUTTON_DOWN_Pin|BUTTON_UP_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_IT_RISING;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOB, &GPIO_InitStruct);

  /* EXTI interrupt init*/
  HAL_NVIC_SetPriority(EXTI1_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI1_IRQn);

  HAL_NVIC_SetPriority(EXTI3_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI3_IRQn);

  HAL_NVIC_SetPriority(EXTI4_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI4_IRQn);

  HAL_NVIC_SetPriority(EXTI9_5_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI9_5_IRQn);

  HAL_NVIC_SetPriority(EXTI15_10_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(EXTI15_10_IRQn);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */
void read_sensors_data(void)
{
    DS3231_GetTime(&timenow);
    TEMP = DS18B20_ReadTemp(&DS1);
}

void process_turbidity(void)
{
    uint32_t avg_adc = Read_ADC_Avg(200);
    float voltage_raw = (avg_adc * 3.3f) / 4095.0f;
    float voltage = voltage_raw + 0.01f; 

    turbidity = -900.4f * (voltage * voltage) - 336.302f * voltage + 2973.295f;

    if (turbidity < 0)
    {
        turbidity = 0;
    }
    else if (turbidity > 1000)
    {
        turbidity = 1000;
    }
}

void measure_food_level(void)
{
    HCSR04_Read();
    percent = ((D_empty - Distance) / (D_empty - D_full)) * 100.0f;

    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;
}

void handle_turbidity_warning(void)
{
    if (turbidity >= 300 && !is_warning_silenced_by_user)
    {
        is_turbidity_warning_active = 1;

				if (HAL_GetTick() - last_beep_toggle_time >= 1000)
				{
						HAL_GPIO_TogglePin(BUZZER_GPIO_Port, BUZZER_Pin); 
						last_beep_toggle_time = HAL_GetTick();
				}
    }
    else
    {
        is_turbidity_warning_active = 0;
        HAL_GPIO_WritePin(BUZZER_GPIO_Port, BUZZER_Pin, GPIO_PIN_RESET);
        
				if (turbidity < 1000) {
            is_warning_silenced_by_user = 0;
        }
    }
}

void handle_uart_transmission(void)
{
    if (HAL_GetTick() - last_uart_send_time >= UART_SEND_INTERVAL)
    {
        snprintf(uart_tx_buffer, sizeof(uart_tx_buffer),
                 "%.1f,%.1f,%.0f,%02d:%02d:%02d\r\n",
                 turbidity,
                 TEMP,
                 percent,
                 timenow.hour,
                 timenow.minutes,
                 timenow.seconds);

        HAL_UART_Transmit(&huart1, (uint8_t*)uart_tx_buffer, strlen(uart_tx_buffer), 1000);
        
        last_uart_send_time = HAL_GetTick();
    }
		HAL_UART_Receive_IT(&huart1, (uint8_t *)&rec, 1);
}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
