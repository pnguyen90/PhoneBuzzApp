
function validate_inputs(){
  var number = document.forms["call_me"]["yournumber"].value;
  var time = document.forms["call_me"]["time"].value;
  var well_formed_number = (number != null && number.length === 12 && number[0] == '+')
  var well_formed_time = (time != null && (time[0] == 's' || time[0] == 'm' || time[0] == 'h'))
  if (well_formed_number && well_formed_time) {
    return true;
  }
  else{
    alert('Make sure your inputs are properly formated. Here is what you entered:' + 'Your number: ' + number + ' Your time delay: ' + time);
    return false;
  }
  return true
}
