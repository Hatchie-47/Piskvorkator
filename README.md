# Piskvorkator
 Bot for jobs.cz piskvorky competition

 Run piskvorkator.py to run a game or reconnect to an unfinihsed one.
 First run will prompt you to register via email and nickname.

 flags:
 -g - Force new game even if one is saved. Use if opponent doesn't play and you want a new game
 -r - Force new registration. Careful, if you do not backup piskvorkator.ini, you will permanently loose your current registration!

 piskvrkator.ini:
 config - Address and player info.
 ai - Parameters to tweak the ai behavior.
 saved -Ssaved game, if there is one piskvorkator will attempt to reconnect.

 ai parameters:
 - 1 and 2 - If piskvorkator goes first it uses parameters ending with 1, if it goes second those ending with 2.
 - defense_parameter - Piskvorkator computes how good a field is for both players and then sums the values. The value for opponent is multiplied by defense_parameter.
 - defense_parameter_tick - The defense parameter for each field is changed by defense_parameter_tick times number of digits in the value.
   By default used to lower defense_parameter for better options so that if Piskvorkator have equaly good options for itself and the opponent, it will choose to further it's gameplay if it's nearing victory.
 - stochastic_rate - After Piskvorkator calculates the final values for each field it finds a maximum value and then considers all values that are within stochastic_rate of the max.
   Default 0.01 meaning 1% - If the maximum value is 1000, any filed with value 990 or higher will be considered, fields with higher values having better odds of being picked.
