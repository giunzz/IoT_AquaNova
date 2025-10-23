#ifndef LCD_STATE_H
#define LCD_STATE_H

typedef enum {
   LCD_STATE_NORMAL,     // Hiển thị nhiệt độ và độ đục
   LCD_STATE_FEEDING,    // Khi bấm BUTTON -> "FEEDING..."
   LCD_STATE_TIMESET,
   LCD_STATE_INFO, 	    // Khi set time
	LCD_STATE_SET,
   LCD_STATE_DISTANCE,
   LCD_STATE_SET_OFF,
   LCD_STATE_LIGHT_ON,
   LCD_STATE_LIGHT_OFF
} LCD_State_t;

/* Khai báo biến toàn cục để các module khác dùng */
extern LCD_State_t lcd_state;
//extern int lcd_timer;
/* Nếu cần, bạn có thể khai báo hàm cập nhật LCD ở đây:
   void LCD_Update(void);
   nhưng nếu hàm này định nghĩa trong main.c và bạn include main.h,
   không bắt buộc. */

#endif /* LCD_STATE_H */
