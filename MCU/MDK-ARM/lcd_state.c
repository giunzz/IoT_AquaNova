#ifndef LCD_STATE_H
#define LCD_STATE_H

typedef enum {
    LCD_STATE_NORMAL,     // Hi?n th? nhi?t d? và d? d?c
    LCD_STATE_FEEDING,    // Khi b?m BUTTON -> "FEEDING..."
    LCD_STATE_TIMESET     // Khi set time
} LCD_State_t;

/* Khai báo bi?n toàn c?c d? các module khác dùng */
extern LCD_State_t lcd_state;

/* N?u c?n, b?n có th? khai báo hàm c?p nh?t LCD ? dây:
   void LCD_Update(void);
   nhung n?u hàm này d?nh nghia trong main.c và b?n include main.h,
   không b?t bu?c. */

#endif /* LCD_STATE_H */
