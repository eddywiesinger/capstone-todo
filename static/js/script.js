$(function($) {
  let url = window.location.href;
  $('.navbar-nav .nav-link').each(function() {
    if (this.href === url) {
      $(this).closest('.nav-item').addClass('active');
    }
  });
});


var password = document.getElementById("password")
  , confirm_password = document.getElementById("confirm_password");

function validatePassword(){
  if(password.value != confirm_password.value) {
    confirm_password.setCustomValidity("Passwords Don't Match");
  } else {
    confirm_password.setCustomValidity('');
  }
}

password.onchange = validatePassword;
confirm_password.onkeyup = validatePassword;