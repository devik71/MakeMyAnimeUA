from magi_pipeline.ass_generator_module.ass_builder import generate_ass
 
class Caspar:
    @staticmethod
    def generate_subtitles(subs, output_path, style_path=None):
        return generate_ass(subs=subs, output_path=output_path, style_path=style_path) 