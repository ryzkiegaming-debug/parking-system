// Convert 24-hour time to 12-hour AM/PM format
function convertTo12Hour(time24) {
  if (!time24) return '';
  
  const [hours24, minutes] = time24.split(':');
  let hours = parseInt(hours24);
  const ampm = hours >= 12 ? 'PM' : 'AM';
  
  hours = hours % 12;
  hours = hours ? hours : 12; // 0 should be 12
  
  return `${hours}:${minutes} ${ampm}`;
}

// Parking slot selection + confirmation flow
(function () {
  let selectedSlot = null;

  function selectSlot(button, allButtons) {
    allButtons.forEach((b) => b.classList.remove("bg-blue-400", "text-white"));
    button.classList.add("bg-blue-400", "text-white");
    selectedSlot = button.textContent.trim();
    window.selectedSlotGlobal = selectedSlot;
    const selectedSpaceInput = document.getElementById("selected_space_input");
    if (selectedSpaceInput) {
      selectedSpaceInput.value = selectedSlot;
    }
    updateReserveButtonEnabled();
  }


  function bindSlotButtons() {
    const slotButtons = Array.from(document.querySelectorAll(".slot"));
    if (!slotButtons.length) {
      return;
    }


    slotButtons.forEach((button) => {
      button.addEventListener("click", () => {
        if (button.disabled) {
          return;
        }
        selectSlot(button, slotButtons);
      });
    });
  }

  
  function showStep2() {
    const entryDateInput = document.getElementById("entry_date");
    const entryTimeInput = document.getElementById("entry_time");
    const exitDateInput = document.getElementById("exit_date");
    const exitTimeInput = document.getElementById("exit_time");

    if (!entryDateInput || !entryTimeInput || !exitDateInput || !exitTimeInput) {
      alert("Booking form is missing required fields.");
      return;
    }

    if (!selectedSlot) {
      alert("Please select a parking slot first!");
      return;
    }

    if (!entryDateInput.value || !entryTimeInput.value || !exitDateInput.value || !exitTimeInput.value) {
      alert("Please complete all date and time fields.");
      return;
    }

    // Validate date/time before proceeding
    if (!validateDateTime()) {
      return;
    }

    const step1 = document.getElementById("step1");
    const step2 = document.getElementById("step2");
    const chosenSlot = document.getElementById("chosenSlot");
    const summaryEntry = document.getElementById("summaryEntry");
    const summaryExit = document.getElementById("summaryExit");
    const selectedSpaceInput = document.getElementById("selected_space_input");

    if (selectedSpaceInput) {
      selectedSpaceInput.value = selectedSlot;
    }

    if (step1) {
      step1.classList.add("hidden");
    }
    if (step2) {
      step2.classList.remove("hidden");
    }
    if (chosenSlot) {
      chosenSlot.textContent = `Parking Slot: ${selectedSlot}`;
    }
    if (summaryEntry) {
      summaryEntry.textContent = `Entry: ${entryDateInput.value} at ${convertTo12Hour(entryTimeInput.value)}`;
    }
    if (summaryExit) {
      summaryExit.textContent = `Exit: ${exitDateInput.value} at ${convertTo12Hour(exitTimeInput.value)}`;
    }
  }

  function backToStep1() {
    const step1 = document.getElementById("step1");
    const step2 = document.getElementById("step2");
    if (step2) {
      step2.classList.add("hidden");
    }
    if (step1) {
      step1.classList.remove("hidden");
    }
  }

  function setCurrentDateTime() {
    const now = new Date();
    
    // Format date as YYYY-MM-DD
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const currentDate = `${year}-${month}-${day}`;
    
    // Format time as HH:MM (round up to next 15 minutes)
    const minutes = now.getMinutes();
    const roundedMinutes = Math.ceil(minutes / 15) * 15;
    now.setMinutes(roundedMinutes);
    now.setSeconds(0);
    
    const hours = String(now.getHours()).padStart(2, '0');
    const mins = String(now.getMinutes()).padStart(2, '0');
    const currentTime = `${hours}:${mins}`;
    
    // Set entry date and time to current
    const entryDateInput = document.getElementById("entry_date");
    const entryTimeInput = document.getElementById("entry_time");
    
    if (entryDateInput) {
      entryDateInput.value = currentDate;
      entryDateInput.min = currentDate; // Prevent past dates
    }
    
    if (entryTimeInput) {
      entryTimeInput.value = currentTime;
    }
    
    // Set exit date to same day, time to 2 hours later
    const exitDate = new Date(now);
    exitDate.setHours(exitDate.getHours() + 2);
    
    const exitDateInput = document.getElementById("exit_date");
    const exitTimeInput = document.getElementById("exit_time");
    
    if (exitDateInput) {
      const exitYear = exitDate.getFullYear();
      const exitMonth = String(exitDate.getMonth() + 1).padStart(2, '0');
      const exitDay = String(exitDate.getDate()).padStart(2, '0');
      exitDateInput.value = `${exitYear}-${exitMonth}-${exitDay}`;
      exitDateInput.min = currentDate; // Prevent past dates
    }
    
    if (exitTimeInput) {
      const exitHours = String(exitDate.getHours()).padStart(2, '0');
      const exitMins = String(exitDate.getMinutes()).padStart(2, '0');
      exitTimeInput.value = `${exitHours}:${exitMins}`;
    }
  }

  function validateDateTime() {
    const entryDateInput = document.getElementById("entry_date");
    const entryTimeInput = document.getElementById("entry_time");
    const exitDateInput = document.getElementById("exit_date");
    const exitTimeInput = document.getElementById("exit_time");
    
    if (!entryDateInput || !entryTimeInput || !exitDateInput || !exitTimeInput) {
      return true;
    }
    
    const entryDateTime = new Date(`${entryDateInput.value}T${entryTimeInput.value}`);
    const exitDateTime = new Date(`${exitDateInput.value}T${exitTimeInput.value}`);
    const now = new Date();
    
    // Allow 2 minutes buffer for past time (accounts for time spent filling form)
    const twoMinutesAgo = new Date(now.getTime() - 2 * 60 * 1000);
    
    // Check if entry is more than 2 minutes in the past
    if (entryDateTime < twoMinutesAgo) {
      showStatus("⚠️ Entry time cannot be in the past", "warning");
      return false;
    }
    
    // Check if entry time is too far in the future (must be within 15 minutes of current time)
    const fifteenMinutesFromNow = new Date(now.getTime() + 15 * 60 * 1000);
    if (entryDateTime > fifteenMinutesFromNow) {
      showStatus("⚠️ Entry time must be within 15 minutes of current time. Please select current time for immediate booking.", "warning");
      return false;
    }
    
    // Check if exit is before entry
    if (exitDateTime <= entryDateTime) {
      showStatus("⚠️ Exit time must be after entry time", "warning");
      return false;
    }
    
    return true;
  }

  // expose for inline onclick handlers if they exist
  window.showStep2 = showStep2;
  window.backToStep1 = backToStep1;

  document.addEventListener("DOMContentLoaded", () => {
    setCurrentDateTime();
    bindSlotButtons();
    
    // Add validation on date/time change
    const dateTimeInputs = [
      document.getElementById("entry_date"),
      document.getElementById("entry_time"),
      document.getElementById("exit_date"),
      document.getElementById("exit_time"),
    ];
    
    dateTimeInputs.forEach((input) => {
      if (input) {
        input.addEventListener("change", () => {
          if (validateDateTime()) {
            checkAvailability();
          }
        });
      }
    });
    
    // Initial availability check
    setTimeout(checkAvailability, 500);
    updateReserveButtonEnabled();
  });
})();

  function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById("availabilityStatus");
    const statusText = document.getElementById("statusText");
    
    if (statusDiv && statusText) {
      statusText.textContent = message;
      statusDiv.classList.remove("hidden", "bg-blue-500/20", "text-blue-200", "bg-green-500/20", "text-green-200", "bg-yellow-500/20", "text-yellow-200");
      
      if (type === 'success') {
        statusDiv.classList.add("bg-green-500/20", "text-green-200");
      } else if (type === 'warning') {
        statusDiv.classList.add("bg-yellow-500/20", "text-yellow-200");
      } else {
        statusDiv.classList.add("bg-blue-500/20", "text-blue-200");
      }
    }
  }

  async function checkAvailability() {
    const entryDateInput = document.getElementById("entry_date");
    const entryTimeInput = document.getElementById("entry_time");
    const exitDateInput = document.getElementById("exit_date");
    const exitTimeInput = document.getElementById("exit_time");

    if (!entryDateInput || !entryTimeInput || !exitDateInput || !exitTimeInput) {
      return;
    }

    const entryDate = entryDateInput.value;
    const entryTime = entryTimeInput.value;
    const exitDate = exitDateInput.value;
    const exitTime = exitTimeInput.value;

    if (!entryDate || !entryTime || !exitDate || !exitTime) {
      showStatus("Select all dates and times to check real-time availability", "info");
      return;
    }

    showStatus("Checking real-time availability...", "info");

    try {
      const response = await fetch('/api/check-availability', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entry_date: entryDate,
          entry_time: entryTime,
          exit_date: exitDate,
          exit_time: exitTime,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        updateSlotAvailability(data.slots);
        updateMapOverlay(data.slots);
        const kpis = data.kpis || {};
        showStatus(`Available: ${kpis.available || 0} • Reserved: ${kpis.reserved || 0} • Occupied: ${kpis.occupied || 0}`, "success");
        updateReserveButtonEnabled();
      } else {
        showStatus("Error checking availability. Please try again.", "warning");
      }
    } catch (error) {
      console.error('Error checking availability:', error);
      showStatus("Error checking availability. Please try again.", "warning");
    }
  }

  function updateSlotAvailability(slots) {
    const slotButtons = document.querySelectorAll(".slot");
    
    slotButtons.forEach((button) => {
      const slotName = button.textContent.trim();
      const slotData = slots.find(s => s.slot_name === slotName);
      
      if (slotData) {
        button.classList.remove("bg-red-500","text-white","cursor-not-allowed","opacity-70","bg-green-300","text-black","bg-blue-400");
        button.style.backgroundColor = '';
        
        // is_available tells us if the slot is available for the REQUESTED time period
        if (slotData.is_available === 1 || slotData.is_available === true) {
          // Available for the requested period - show as green and enable
          button.classList.add("bg-green-300","text-black");
          button.disabled = false;
          button.removeAttribute("aria-disabled");
        } else {
          // Not available for the requested period - show as red and disable
          button.classList.add("bg-red-500","text-white","cursor-not-allowed","opacity-70");
          button.disabled = true;
          button.setAttribute("aria-disabled","true");
          if (window.selectedSlotGlobal === slotName) {
            window.selectedSlotGlobal = null;
          }
        }
      }
    });
  }

  function updateMapOverlay(slots) {
    const overlay = document.getElementById("mapOverlay");
    if (!overlay) return;
    const markers = overlay.querySelectorAll('[data-slot]');
    markers.forEach((el) => {
      const name = el.getAttribute('data-slot');
      // No conversion needed - map markers use P1-P10, same as database
      const slot = slots.find(s => s.slot_name === name);
      el.classList.remove('bg-green-300','bg-red-500');
      el.style.backgroundColor = '';
      if (slot) {
        // Use is_available to determine if slot is available for requested period
        if (slot.is_available === 1 || slot.is_available === true) {
          el.classList.add('bg-green-300');
        } else {
          el.classList.add('bg-red-500');
        }
      } else {
        el.classList.add('bg-green-300');
      }
      el.onclick = () => {
        const btn = Array.from(document.querySelectorAll('.slot')).find(b => b.textContent.trim() === name);
        if (btn && !btn.disabled) {
          btn.click();
        }
      };
    });
  }

  function setCurrentDateTime() {
    const now = new Date();
    
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const currentDate = `${year}-${month}-${day}`;
    
    // Use exact current time (no rounding)
    const hours = String(now.getHours()).padStart(2, '0');
    const mins = String(now.getMinutes()).padStart(2, '0');
    const currentTime = `${hours}:${mins}`;
    
    const entryDateInput = document.getElementById("entry_date");
    const entryTimeInput = document.getElementById("entry_time");
    
    if (entryDateInput) {
      entryDateInput.value = currentDate;
      entryDateInput.min = currentDate;
    }
    
    if (entryTimeInput) {
      entryTimeInput.value = currentTime;
    }
    
    const exitDate = new Date(now);
    exitDate.setHours(exitDate.getHours() + 2);
    
    const exitDateInput = document.getElementById("exit_date");
    const exitTimeInput = document.getElementById("exit_time");
    
    if (exitDateInput) {
      const exitYear = exitDate.getFullYear();
      const exitMonth = String(exitDate.getMonth() + 1).padStart(2, '0');
      const exitDay = String(exitDate.getDate()).padStart(2, '0');
      exitDateInput.value = `${exitYear}-${exitMonth}-${exitDay}`;
      exitDateInput.min = currentDate;
    }
    
    if (exitTimeInput) {
      const exitHours = String(exitDate.getHours()).padStart(2, '0');
      const exitMins = String(exitDate.getMinutes()).padStart(2, '0');
      exitTimeInput.value = `${exitHours}:${exitMins}`;
    }
  }

  function validateDateTime() {
    const entryDateInput = document.getElementById("entry_date");
    const entryTimeInput = document.getElementById("entry_time");
    const exitDateInput = document.getElementById("exit_date");
    const exitTimeInput = document.getElementById("exit_time");
    
    if (!entryDateInput || !entryTimeInput || !exitDateInput || !exitTimeInput) {
      return true;
    }
    
    const entryDateTime = new Date(`${entryDateInput.value}T${entryTimeInput.value}`);
    const exitDateTime = new Date(`${exitDateInput.value}T${exitTimeInput.value}`);
    const now = new Date();
    
    if (entryDateTime < now) {
      showStatus("⚠️ Entry time cannot be in the past", "warning");
      return false;
    }
    
    if (exitDateTime <= entryDateTime) {
      showStatus("⚠️ Exit time must be after entry time", "warning");
      return false;
    }
    
    return true;
  }

  // Initialize on page load
  if (document.readyState === 'loading') {
    document.addEventListener("DOMContentLoaded", () => {
      setCurrentDateTime();
      
      const dateTimeInputs = [
        document.getElementById("entry_date"),
        document.getElementById("entry_time"),
        document.getElementById("exit_date"),
        document.getElementById("exit_time"),
      ];
      
      dateTimeInputs.forEach((input) => {
        if (input) {
          input.addEventListener("change", () => {
            if (validateDateTime()) {
              checkAvailability();
            }
          });
        }
      });
      
      setTimeout(checkAvailability, 500);
    });
  } else {
    setCurrentDateTime();
    setTimeout(checkAvailability, 500);
  }
  function updateReserveButtonEnabled() {
    const btn = document.getElementById("reserveBtn");
    if (!btn) return;
    const slotButtons = Array.from(document.querySelectorAll('.slot'));
    const currentSelected = window.selectedSlotGlobal;
    const selectedButton = slotButtons.find(b => b.textContent.trim() === currentSelected);
    const entryDateInput = document.getElementById("entry_date");
    const entryTimeInput = document.getElementById("entry_time");
    const exitDateInput = document.getElementById("exit_date");
    const exitTimeInput = document.getElementById("exit_time");
    const hasDates = entryDateInput && entryTimeInput && exitDateInput && exitTimeInput && entryDateInput.value && entryTimeInput.value && exitDateInput.value && exitTimeInput.value;
    const enabled = !!currentSelected && !!selectedButton && !selectedButton.disabled && !!hasDates;
    btn.disabled = !enabled;
  }

  const reserveBtn = document.getElementById('reserveBtn');
  if (reserveBtn) {
    reserveBtn.addEventListener('click', (e) => {
      if (!validateDateTime()) {
        e.preventDefault();
        return;
      }
      if (!window.selectedSlotGlobal) {
        e.preventDefault();
        alert('Please select a parking slot first!');
        return;
      }
    });
  }
