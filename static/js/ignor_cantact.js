    var ignor_etebar = document.getElementById("ignor_etebar");
    console.log(ignor_etebar.innerHTML);
    if ( ignor_etebar.innerHTML == 'empty' ){
        Swal.fire('لطفا کد ملی را وارد کنید');
    }

    if ( ignor_etebar.innerHTML == 'nonempty' ){
        Swal.fire({
  icon: 'error',
  title: 'کد ملی وارد شده تاکنون ثبت نام نکرده است',
  text: 'لطفا ثبت نام کنید',
  // showDenyButton: true,
  // showCancelButton: true,
  confirmButtonText: 'ثبت نام',
  // denyButtonText: `Don't save`,
}).then((result) => {
  /* Read more about isConfirmed, isDenied below */
  if (result.isConfirmed) {
    window.location = "/cantact/addcontact/";
  }
  // else if (result.isDenied) {
  //   Swal.fire('Changes are not saved', '', 'info')
  // }
});
        // window.location = "/cantact/addcontact/";

    }

    if ( ignor_etebar.innerHTML == 'succes' ){
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

