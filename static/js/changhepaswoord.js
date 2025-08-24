var etebar = document.getElementById("etebar");
    if ( etebar.innerHTML == 'succes' ){
        Swal.fire({
          position: 'top-end',
          icon: 'success',
          title: 'رمز با موفقیت تغییر کرد',
          showConfirmButton: false,
          timer: 2000
                 });
        setTimeout('redirectt()',500);
    }


    function redirectt()
    {
        window.location = "/";
    }
