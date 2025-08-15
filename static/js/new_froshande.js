document.addEventListener('DOMContentLoaded', function() {
  // اعتبارسنجی شماره موبایل
  // const mobileInput = document.getElementById('mobile');
  // if (mobileInput) {
  //   mobileInput.addEventListener('blur', function() {
  //     const regex = /^09\d{9}$/;
  //     if (this.value && !regex.test(this.value)) {
  //       showError(this, 'شماره موبایل باید با 09 شروع شده و 11 رقمی باشد');
  //     } else {
  //       clearError(this);
  //     }
  //   });
  // }
  //
  // // اعتبارسنجی شماره شبا
  // const shebaInput = document.getElementById('sheba_number');
  // if (shebaInput) {
  //   shebaInput.addEventListener('blur', function() {
  //     const regex = /^IR[0-9]{24}$/;
  //     if (this.value && !regex.test(this.value)) {
  //       showError(this, 'شماره شبا باید با IR شروع شده و 26 کاراکتر داشته باشد');
  //     } else {
  //       clearError(this);
  //     }
  //   });
  // }

  // اعتبارسنجی شماره کارت
  const cardInput = document.getElementById('card_number');
  if (cardInput) {
    cardInput.addEventListener('blur', function() {
      if (this.value && this.value.length !== 16) {
        showError(this, 'شماره کارت باید 16 رقمی باشد');
      } else {
        clearError(this);
      }
    });
  }

  // اعتبارسنجی فرم هنگام ارسال
  const form = document.querySelector('.signup-form');
  if (form) {
    form.addEventListener('submit', function(e) {
      let isValid = true;
      const requiredFields = document.querySelectorAll('input[required]');

      requiredFields.forEach(field => {
        if (!field.value.trim()) {
          showError(field, 'این فیلد اجباری است');
          isValid = false;
        }
      });

      if (!isValid) e.preventDefault();
    });
  }

  // نمایش خطا
  function showError(input, message) {
    clearError(input);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    input.parentNode.appendChild(errorDiv);
    input.style.borderColor = 'var(--error-color)';
  }

  // پاک کردن خطا
  function clearError(input) {
    const errorDiv = input.parentNode.querySelector('.error-message');
    if (errorDiv) errorDiv.remove();
    input.style.borderColor = '';
  }
});
// تابع تبدیل اعداد فارسی/عربی به انگلیسی
function convertToEnglishDigits(input) {
    const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    const arabicDigits = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    let output = '';

    for (let char of input) {
        if (persianDigits.includes(char)) {
            output += persianDigits.indexOf(char);
        } else if (arabicDigits.includes(char)) {
            output += arabicDigits.indexOf(char);
        } else {
            output += char;
        }
    }

    return output;
}

// اعمال تبدیل برای فیلدهای مورد نظر هنگام ارسال فرم
$(document).ready(function() {
    $('.signup-form').submit(function(e) {
        const numberFields = [
            '#mobile',
            '#card_number',
            '#sheba_number',
            '#phone'
        ];

        numberFields.forEach(field => {
            const $input = $(field);
            $input.val(convertToEnglishDigits($input.val()));
        });
    });
});