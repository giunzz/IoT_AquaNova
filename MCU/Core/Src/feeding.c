/*
 * feeding.c
 *
 *  Created on: Sep 15, 2025
 *      Author: NHU Y
 */
#include "feeding.h"
#include "lcd_state.h"
#include <string.h>

int lcd_timer = 0; 
//extern char lcd_info_buffer[];
struct feeding_t *_feed;

DS3231_Time_t settime = {
		.seconds = 0,
		.minutes = 48,
		.hour = 9,
		.dayofweek = 5,
		.dayofmonth = 23,
		.month = 10,
		.year = 25
};

static void feeding_Servo_Angle(int16_t angle);

void feeding_Alarm(void)
{
	_feed->IsFeed = 1;            
	lcd_state = LCD_STATE_FEEDING;  
	lcd_timer = HAL_GetTick();      
}

void feeding_ISR(uint16_t GPIO_Pin) {
	
	// chong bouncing
	static uint32_t last_interrupt_time = 0;
  if (HAL_GetTick() - last_interrupt_time < 250) {
      return; 
  }
  last_interrupt_time = HAL_GetTick();
	
	
	if (GPIO_Pin == BUTTON_Pin) {
		if(_feed->IsSetTime == 0)
		{
			_feed->IsFeed = 1;
			lcd_state = LCD_STATE_FEEDING;
			lcd_timer = HAL_GetTick();
		}
		else
		{
			_feed->IsSetTime = 2;
			_feed->IsAlarmEnabled = 1;   // thong bao da set gio
			lcd_state = LCD_STATE_SET;
			lcd_timer = HAL_GetTick();
		}
	}
	if (GPIO_Pin == BUTTON_OFF_Pin) {
		if(_feed->IsSetTime == 1)
		{
			_feed->IsSetTime = 0; 		
			_feed->IsAlarmEnabled = 0; 	
			lcd_state = LCD_STATE_SET_OFF; 
			lcd_timer = HAL_GetTick(); 	
		}
	}	
	if (GPIO_Pin == ALARM_Pin) {
		uint8_t status;
		HAL_I2C_Mem_Read(_feed->hi2c, 0xD0, 0x0F, 1, &status, 1, 1000);
		status &= ~(1<<0);
		HAL_I2C_Mem_Write(_feed->hi2c, 0xD0, 0x0F, 1, &status, 1, 1000);
		HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
		_feed->IsFeed = 1;
		lcd_state = LCD_STATE_FEEDING;
    lcd_timer = HAL_GetTick();
		_feed->IsSetTime = 0;
		_feed->IsAlarmEnabled = 0;
	}
	if (GPIO_Pin == BUTTON_UP_Pin) {
		_feed->IsSetTime = 1;
		_feed->alarm_time.hour++;
		if (_feed->alarm_time.hour >= 24) _feed->alarm_time.hour = 0;	
		lcd_state = LCD_STATE_TIMESET;
		lcd_timer = HAL_GetTick();
	}
	if (GPIO_Pin == BUTTON_DOWN_Pin) {
		_feed->IsSetTime = 1;
		_feed->alarm_time.hour--;
		if (_feed->alarm_time.hour < 0) _feed->alarm_time.hour = 23;
		lcd_state = LCD_STATE_TIMESET;
		lcd_timer = HAL_GetTick();
	}
	
	if (GPIO_Pin == BUTTON_CONTROL_Pin) {
		
//		if(HAL_GetTick() - debounce_timer < 200) return;
//		debounce_timer = HAL_GetTick();
		if (lcd_state == LCD_STATE_NORMAL)
		{
			lcd_state = LCD_STATE_INFO;
		} else  if (lcd_state == LCD_STATE_INFO)
		{
			lcd_state = LCD_STATE_DISTANCE;
		} 
		else
		{
			lcd_state = LCD_STATE_NORMAL;
		}
		lcd_timer = HAL_GetTick();
	}
}

void feeding_Servo_Spin(uint32_t delay_time) {
    switch(_feed->IsFeed) {
        case 1:
            feeding_Servo_Angle(30);
            _feed->IsFeed = 2;
            break;
        case 3:
            feeding_Servo_Angle(5);
    		_feed->IsFeed = 0;
        	break;
    }
}

void feeding_Handler(void) {
	if (_feed->IsFeed != 0){
		feeding_Servo_Spin(1000);
	}
	if (_feed->IsSetTime == 2){
		// Send feed schedule alarm
		DS3231_SetAlarm(_feed->alarm_time);
		_feed->IsSetTime = 0;
	}
}

void feeding_Init(struct feeding_t *feed) {
	_feed = feed;
	DS3231_Init(_feed->hi2c);
	HAL_TIM_PWM_Start(_feed->htim, _feed->channel);
	feeding_Servo_Angle(0);
	
	_feed->IsAlarmEnabled = 0; // chua hen gio
	
	uint8_t control_reg = 0x05; 
	uint8_t status_reg = 0x00;  // xoa bao thuc cu

	// bao da ngat bao thuc
	HAL_I2C_Mem_Write(_feed->hi2c, 0xD0, 0x0E, 1, &control_reg, 1, 1000);

	// xoa trang thai cu
	HAL_I2C_Mem_Write(_feed->hi2c, 0xD0, 0x0F, 1, &status_reg, 1, 1000);
	

	//DS3231_SetTime(settime);
}

static void feeding_Servo_Angle(int16_t angle) {
	if(angle > 180) angle = 180;
	if(angle < 5) angle = 5 ;

	int duty = -(angle * 50/9) + 1250;
	__HAL_TIM_SET_COMPARE(_feed->htim, _feed->channel, duty);
	_feed->angle = angle;
}

/* Unused */

