
    var etebar = document.getElementById("melicod_etebar");
    if ( etebar.innerHTML == 'false' ){ mymessage()}

    function mymessage(){
        Swal.fire({
              icon: 'هشدار',
              title: 'کد ملی وارد شده قبلا ثبت شده است',
              text: 'برای ورود یا بازیابی رمز از لینک زیر استفاده کنید',
              footer: '<a href="/cantact/login/">ورود و بازیابی رمز</a>'
})
    }

    if ( etebar.innerHTML == 'empty')
    {
        Swal.fire({
            icon: 'warning',
            title: 'لطفا کد ملی را وارد کنید'
        })

    }
    if ( etebar.innerHTML == 'repeat')
    {
        Swal.fire({
            icon: 'warning',
            title: 'کد ملی معتبر نمیباشد'
        })
    }
    if ( etebar.innerHTML == 'stringerror')
    {
        Swal.fire({
            icon: 'warning',
            title: 'لطفا اعداد را انگلیسی وارد کنید'
        })

    }
    if ( etebar.innerHTML == 'tellerror')
    {
        Swal.fire({
            icon: 'warning',
            title: 'شماره تلفن اشتباه وارد شده است'
        })

    }


    if ( etebar.innerHTML == 'neterror')
    {
        Swal.fire({
            icon: 'warning',
            title: 'شبکه اینترنت شما متصل نمیشود'
        })

    }

    function citylist()
{
        f = document.getElementById("face");
        f.click();
}
 function move() {
    var elem = document.getElementById("myBar");
    var width = 0;
    var id = setInterval(frame, 100);
    function frame() {
      if (width >= 100) {
        clearInterval(id);
        elem.hidden=true
      } else {
        width++;
        elem.style.width = width + '%';
        elem.innerHTML = width * 1  + '%';
        elem.hidden=false
      }
    }
  }

document.querySelector('.custom-select').addEventListener('click',function() { this.querySelector('.select-items').classList.toggle('select-hide');});


