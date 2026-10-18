/* اسکریپت‌های عمومی سامانه امغازی */

// منوی موبایل و جزئیات متفرقه
document.addEventListener('DOMContentLoaded', function () {
  // تأیید حذف
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      if (!window.confirm(form.getAttribute('data-confirm') || 'آیا مطمئن هستید؟')) {
        e.preventDefault();
      }
    });
  });

  // نمایش پیش‌نمایش انتخاب خدمت در فرم رزرو
  var serviceSelect = document.getElementById('service_id');
  if (serviceSelect) {
    var priceHint = document.getElementById('price-hint');
    serviceSelect.addEventListener('change', function () {
      var opt = serviceSelect.options[serviceSelect.selectedIndex];
      if (priceHint && opt && opt.dataset.price !== undefined) {
        priceHint.textContent = opt.dataset.price;
      }
    });
  }
});
