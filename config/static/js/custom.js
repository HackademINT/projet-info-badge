function flash_sweetalert2(text, title, category) {
  Swal.fire({
    type: category,
    title: title,
    html: text,
  })
}
