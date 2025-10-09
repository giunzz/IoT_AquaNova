/*
 * DS3231.h
 *
 *  Created on: Nov 29, 2022
 *      Author: anh
 */

#ifndef DS3231_H_
#define DS3231_H_
#include "main.h"
#define DS3231_ADDRESS 0xD0

typedef struct {
	int8_t seconds;
	int8_t minutes;
	int8_t hour;
	int8_t dayofweek;
	int8_t dayofmonth;
	int8_t month;
	int8_t year;
} DS3231_Time_t;


void DS3231_Init(I2C_HandleTypeDef *i2c);

void DS3231_SetTime(DS3231_Time_t time);
void DS3231_GetTime(DS3231_Time_t *time);
void DS3231_SetAlarm(DS3231_Time_t time);

float DS3231_GetTemp(void);


#endif /* DS3231_H_ */
