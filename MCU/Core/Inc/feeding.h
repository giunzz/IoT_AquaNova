/*
 * feeding.h
 *
 *  Created on: Sep 15, 2025
 *      Author: NHU Y
 */

#ifndef INC_FEEDING_H_
#define INC_FEEDING_H_

#include "main.h"
#include "DS3231.h"

#define SERVO_ANGLE_0	750
#define SERVO_ANGLE_45	500
#define SERVO_ANGLE_90	250

#define FEEDING_WAIT	1000

struct feeding_t {
	I2C_HandleTypeDef *hi2c;
	TIM_HandleTypeDef *htim;
	uint32_t channel;
	uint16_t angle;
	uint8_t IsFeed;		/* 0: chưa cho ăn / 1: quay 180 độ / 2: chờ 1s / 3: quay về 0 độ */
	uint8_t IsSetTime;	/* 0: Cho ăn / 1: Chỉnh giờ / 2: Hẹn giờ */
	uint8_t IsAlarmEnabled; // bao da set thoi gian
	DS3231_Time_t alarm_time;
};

void feeding_Init(struct feeding_t *feed);
void feeding_Handler(void);
void feeding_ISR(uint16_t GPIO_Pin);
void feeding_Alarm(void);
extern int lcd_timer;
#endif /* INC_FEEDING_H_ */
