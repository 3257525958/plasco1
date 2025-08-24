var minutes;
var seconds;
var set_inteval;
var etebar = document.getElementById("etebar");

function otp_timer() {
    if (seconds == 0 & minutes == 0) {
        document.getElementById('seconds').innerHTML = '00';
        document.getElementById('minutes').innerHTML = '0';
        document.getElementById('regesterbuttonrepeat').disabled = false;
        document.getElementById('regesterbuttonsave').disabled = true;

    } else {
        seconds -= 1;
        document.getElementById('seconds').innerHTML = seconds;
        document.getElementById('minutes').innerHTML = minutes;
            if (seconds == 0) {
            if (minutes > 0) {
                seconds = 60;
                minutes -= 1;
            } else {
                document.getElementById("sendButton1").disabled = true;
                minutes = 0;
                document.getElementById('minutes').innerHTML = minutes;
                clearInterval(set_inteval);
                minutes = 0;
                seconds = 0;
                document.getElementById('seconds').innerHTML = '00';
                document.getElementById('minutes').innerHTML = '0';
            }
        }
    }
}
function startTimer()
{
    document.getElementById('regesterbuttonrepeat').disabled = true;
    // document.getElementById('regesterbuttonsave').disabled = false;
    minutes = 0;
    seconds = 59;
    document.getElementById('seconds').innerHTML = seconds;
    document.getElementById('minutes').innerHTML = minutes;
    set_inteval = setInterval( 'otp_timer()', 1000 );
}
startTimer();



        console.log(etebar.innerHTML);
if ( etebar.innerHTML == 'succes' ){
        Swal.fire({
          position: 'top-end',
          icon: 'success',
          title: 'با موفقیت وارد شدید',
          showConfirmButton: false,
          timer: 2000
                 });
        setTimeout('redirectt()',500);
    }


    function redirectt()
    {
        window.location = "/";
    }


    if ( etebar.innerHTML == 'false' ){
        Swal.fire('رمز اشتباه است یک دقیقه دیگر رمز جدید دریافت کنید')
    }

 function move(){
    var el = document.getElementById("myBar");
    var width = 0;
    var id = setInterval(frame, 100);
    function frame() {
      if (width >= 100) {
        clearInterval(id);
        el.hidden=true
      } else {
        width++;
        el.style.width = width + '%';
        el.innerHTML = width * 1  + '%';
        el.hidden=false
      }
    }
  }

