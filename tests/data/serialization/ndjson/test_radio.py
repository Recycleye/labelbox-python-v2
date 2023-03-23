import json
from labelbox.data.annotation_types.annotation import ClassificationAnnotation
from labelbox.data.annotation_types.classification.classification import ClassificationAnswer
from labelbox.data.annotation_types.classification.classification import Radio
from labelbox.data.annotation_types.data.text import TextData
from labelbox.data.annotation_types.label import Label

from labelbox.data.serialization.ndjson.converter import NDJsonConverter


def test_serialization_with_radio_min():
    label = Label(
        uid="ckj7z2q0b0000jx6x0q2q7q0d",
        data=TextData(
            uid="bkj7z2q0b0000jx6x0q2q7q0d",
            text="This is a test",
        ),
        annotations=[
            ClassificationAnnotation(
                name="radio_question_geo",
                value=Radio(
                    answer=ClassificationAnswer(name="first_radio_answer",)))
        ])

    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)
    assert res['name'] == "radio_question_geo"
    assert res['answer']['name'] == "first_radio_answer"
    assert res['dataRow']['id'] == "bkj7z2q0b0000jx6x0q2q7q0d"

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    annotation = res.annotations[0]

    annotation_value = annotation.value
    assert type(annotation_value) is Radio
    assert annotation_value.answer.name == "first_radio_answer"


def test_serialization_with_radio_classification():
    label = Label(uid="ckj7z2q0b0000jx6x0q2q7q0d",
                  data=TextData(
                      uid="bkj7z2q0b0000jx6x0q2q7q0d",
                      text="This is a test",
                  ),
                  annotations=[
                      ClassificationAnnotation(
                          name="radio_question_geo",
                          confidence=0.5,
                          value=Radio(answer=ClassificationAnswer(
                              confidence=0.6,
                              name="first_radio_answer",
                              classifications=[
                                  ClassificationAnnotation(
                                      name="sub_radio_question",
                                      value=Radio(answer=ClassificationAnswer(
                                          name="first_sub_radio_answer")))
                              ])))
                  ])

    serialized = NDJsonConverter.serialize([label])
    res = next(serialized)
    assert res['confidence'] == 0.5
    assert res['name'] == "radio_question_geo"
    assert res['answer']['name'] == "first_radio_answer"
    assert res['answer']['confidence'] == 0.6
    assert res['dataRow']['id'] == "bkj7z2q0b0000jx6x0q2q7q0d"

    classification = res['answer']['classifications'][0]
    assert classification['name'] == "sub_radio_question"
    assert classification['answer']['name'] == "first_sub_radio_answer"

    deserialized = NDJsonConverter.deserialize([res])
    res = next(deserialized)
    annotation = res.annotations[0]
    assert annotation.confidence == 0.5

    annotation_value = annotation.value
    assert type(annotation_value) is Radio
    assert annotation_value.answer.name == "first_radio_answer"
    assert annotation_value.answer.confidence == 0.6

    classification = annotation_value.answer.classifications[0]
    assert type(classification) is ClassificationAnnotation
    assert classification.name == "sub_radio_question"
    assert classification.value.answer.name == "first_sub_radio_answer"
