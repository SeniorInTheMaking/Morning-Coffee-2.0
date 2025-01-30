import datetime

def write_log(object, description):
    file = open('log', 'a')

    time = str(datetime.datetime.now().today().replace(microsecond=0))
    note = time + ' ' + str(object) + ' ' + description

    file.write(note)
    file.write('\n')
    file.close()