/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
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

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f1xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define LED_Pin GPIO_PIN_13
#define LED_GPIO_Port GPIOC
#define TURB_Pin GPIO_PIN_1
#define TURB_GPIO_Port GPIOA
#define ECHO_Pin GPIO_PIN_4
#define ECHO_GPIO_Port GPIOA
#define TRIG_HCSR04_Pin GPIO_PIN_5
#define TRIG_HCSR04_GPIO_Port GPIOA
#define BUZZER_Pin GPIO_PIN_6
#define BUZZER_GPIO_Port GPIOA
#define LIGHT_Pin GPIO_PIN_7
#define LIGHT_GPIO_Port GPIOA
#define ALARM_Pin GPIO_PIN_1
#define ALARM_GPIO_Port GPIOB
#define ALARM_EXTI_IRQn EXTI1_IRQn
#define DS18B20_Pin GPIO_PIN_15
#define DS18B20_GPIO_Port GPIOB
#define BUTTON_OFF_Pin GPIO_PIN_15
#define BUTTON_OFF_GPIO_Port GPIOA
#define BUTTON_OFF_EXTI_IRQn EXTI15_10_IRQn
#define BUTTON_CONTROL_Pin GPIO_PIN_3
#define BUTTON_CONTROL_GPIO_Port GPIOB
#define BUTTON_CONTROL_EXTI_IRQn EXTI3_IRQn
#define BUTTON_DOWN_Pin GPIO_PIN_4
#define BUTTON_DOWN_GPIO_Port GPIOB
#define BUTTON_DOWN_EXTI_IRQn EXTI4_IRQn
#define BUTTON_UP_Pin GPIO_PIN_5
#define BUTTON_UP_GPIO_Port GPIOB
#define BUTTON_UP_EXTI_IRQn EXTI9_5_IRQn
#define BUTTON_Pin GPIO_PIN_8
#define BUTTON_GPIO_Port GPIOB
#define BUTTON_EXTI_IRQn EXTI9_5_IRQn
#define SERVO_Pin GPIO_PIN_9
#define SERVO_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
