
function sideframeCloseHandler(event) {
  try {
    window.top.CMS.API.Sideframe.close();
  } catch (event) {}
}

document.addEventListener('DOMContentLoaded', function(event) {
  /* Close the Sideframe on click */
  const triggerList = document.querySelectorAll('.js-djangocms-references-close-sideframe');

  triggerList.forEach(function(trigger) {
      trigger.addEventListener('click', sideframeCloseHandler);
  });
});
