from mir.io import FeatureIO
import jams


class JamsIO(FeatureIO):
    def read(self, filename, entry):
        return jams.load(filename)

    def write(self, data : jams.JAMS, filename, entry):
        data.save(filename)

    def visualize(self, data : jams.JAMS, filename, entry, override_sr):
        f=open(filename,'w')
        for annotation in data.annotations:
            for obs in annotation.data:
                f.write('%f\t%f\t%s\n'%(obs.time,obs.time+obs.duration,str(obs.value)))
        f.close()
