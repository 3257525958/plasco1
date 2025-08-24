document.addEventListener('DOMContentLoaded', function () {
  // مقداردهی اولیه تقویم تاریخ شمسی برای فیلد تاریخ تولد
  $("#birthdate").persianDatepicker({
    observer: true,
    format: 'YYYY/MM/DD',
    autoClose: true,
    initialValue: false,
    onSelect: function (unix) {
      let date = new persianDate(unix);
      let formattedDate = date.format("YYYY/MM/DD");
      document.getElementById('birthdate').value = formattedDate;

      // تنظیم مقادیر مخفی برای روز، ماه و سال (اختیاری)
      let parts = formattedDate.split("/");
      document.getElementById('year').value = parts[0];
      document.getElementById('month').value = parts[1];
      document.getElementById('day').value = parts[2];
    }
  });

  // نمایش تقویم هنگام کلیک روی آیکون تقویم
  document.getElementById('calendar-icon').addEventListener('click', function () {
    $("#birthdate").persianDatepicker('show');
  });

  // اعتبارسنجی شماره تلفن هنگام ارسال فرم
  document.querySelector('.signup-form').addEventListener('submit', function (e) {
    const phone = document.getElementById('phone').value;
    if (!/^09\d{9}$/.test(phone)) {
      e.preventDefault();
      Swal.fire({
        icon: 'error',
        title: 'شماره موبایل نامعتبر',
        text: 'لطفاً شماره موبایل را به صورت صحیح وارد کنید (09xxxxxxxxx)'
      });
    }
  });
});

    if ( login_etebar.innerHTML == 'false_in_paswoord' ){
        Swal.fire({
            icon: 'هشدار',
            title: 'رمز اشتباه است',
            text: 'برای ورود یا بازیابی رمز از لینک زیر استفاده کنید',
            footer: '<a href="/cantact/ignor/">فراموشی رمز</a>'
});
    }


    if ( login_etebar.innerHTML == 'false' ){
                Swal.fire({
              icon: 'هشدار',
              title: 'این کد ملی تاکنون ثبت نام نکرده است',
              text: 'برای ثبت نام از لینک زیر استفاده کنید',
              footer: '<a href="/cantact/addcontact/">ثبت نام </a>'
});
    }


    if ( login_etebar.innerHTML == 'empty' ){

        Swal.fire('لطفا کد ملی را وارد کنید');

    }


    if ( login_etebar.innerHTML == 'true' ){
        Swal.fire({
          position: 'top-end',
          icon: 'success',
          title: 'با موفقیت وارد شدید',
          showConfirmButton: false,
          timer: 4000
                 });


    setTimeout('redirectt()',2500);
    }


    function redirectt()
    {
        window.location = "/";
    }




    // --------------------------------------
etebar_edit = document.getElementById("etebar_edit");
        console.log(etebar_edit.innerHTML);
if ( etebar_edit.innerHTML == 'succes' ){
        Swal.fire({
          position: 'top-end',
          icon: 'success',
          title: 'ویرایش با موفقیت انجام شد',
          showConfirmButton: false,
          timer: 2000
                 });
        setTimeout('redirectt()',500);
    }

if (etebar_edit.innerHTML == 'ok' ){
        Swal.fire({
          position: 'top-end',
          icon: 'success',
          title: 'ویرایش با موفقیت انجام شد',
          showConfirmButton: false,
          timer: 2000
                 });
        setTimeout('profile()',500);
    }
    function profile()
    {
        window.location = "/reserv/member_profile/";
    }
