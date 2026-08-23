import React from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css"
import { useState } from "react";
function MeWhenDate ({selectedDate, setSelectedDate})
{
    const handleDateChange=(date)=>
        {
            setSelectedDate(date);
        }
    return(
    <div>
        <p>Please enter the date you want</p>
    <DatePicker
    selected={selectedDate} onChange={handleDateChange} dateFormat="MM//dd//YYYY"
    />
    </div>
    )
}
export default MeWhenDate;