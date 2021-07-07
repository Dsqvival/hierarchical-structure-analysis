NUM_TO_ABS_SCALE=['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B']

def get_scale_and_suffix(name):
    result="C*D*EF*G*A*B".index(name[0])
    prefix_length=1
    if (len(name) > 1):
        if (name[1] == 'b'):
            result = result - 1
            if (result<0):
                result+=12
            prefix_length=2
        if (name[1] == '#'):
            result = result + 1
            if (result>=12):
                result-=12
            prefix_length=2
    return result,name[prefix_length:]

def scale_name_to_value(name):
    result="1*2*34*5*6*78*9".index(name[-1]) # 8 and 9 are for weird tagging in some mirex chords
    return (result-name.count('b')+name.count('#')+12)%12
